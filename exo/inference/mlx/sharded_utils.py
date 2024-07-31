# Adapted from https://github.com/ml-explore/mlx-examples/blob/main/llms/mlx_lm/utils.py

import glob
import importlib
import json
import logging
import asyncio
import aiohttp
from functools import partial
from pathlib import Path
from typing import Optional, Tuple, Union, List, Callable
from PIL import Image
from io import BytesIO
import base64
import os

from exo import DEBUG
import mlx.core as mx
import mlx.nn as nn
from huggingface_hub import snapshot_download, list_repo_tree, get_paths_info
from huggingface_hub.utils import filter_repo_objects
from huggingface_hub.file_download import repo_folder_name
from huggingface_hub.constants import HF_HUB_CACHE
from huggingface_hub.utils._errors import RepositoryNotFoundError
from transformers import AutoProcessor

from mlx_lm.tokenizer_utils import load_tokenizer, TokenizerWrapper
from mlx_lm.tuner.utils import apply_lora_layers

from ..shard import Shard


class ModelNotFoundError(Exception):
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)


MODEL_REMAPPING = {
  "mistral": "llama",  # mistral is compatible with llama
  "phi-msft": "phixtral",
}


def _get_classes(config: dict):
  """
  Retrieve the model and model args classes based on the configuration.

  Args:
   config (dict): The model configuration.

  Returns:
   A tuple containing the Model class and the ModelArgs class.
  """
  model_type = config["model_type"]
  model_type = MODEL_REMAPPING.get(model_type, model_type)
  try:
    arch = importlib.import_module(f"exo.inference.mlx.models.{model_type}")
  except ImportError:
    msg = f"Model type {model_type} not supported."
    logging.error(msg)
    raise ValueError(msg)

  return arch.Model, arch.ModelArgs


def load_config(model_path: Path) -> dict:
  try:
    with open(model_path / "config.json", "r") as f:
      config = json.load(f)
  except FileNotFoundError:
    logging.error(f"Config file not found in {model_path}")
    raise
  return config


def load_model_shard(
  model_path: Path,
  shard: Shard,
  lazy: bool = False,
  model_config: dict = {},
) -> nn.Module:
  """
  Load and initialize the model from a given path.

  Args:
   model_path (Path): The path to load the model from.
   lazy (bool): If False eval the model parameters to make sure they are
    loaded in memory before returning, otherwise they will be loaded
    when needed. Default: ``False``
   model_config(dict, optional): Configuration parameters for the model.
    Defaults to an empty dictionary.

  Returns:
   nn.Module: The loaded and initialized model.

  Raises:
   FileNotFoundError: If the weight files (.safetensors) are not found.
   ValueError: If the model class or args class are not found or cannot be instantiated.
  """
  config = load_config(model_path)
  config.update(model_config)

  # TODO hack
  config["shard"] = {
    "model_id": model_path.name,
    "start_layer": shard.start_layer,
    "end_layer": shard.end_layer,
    "n_layers": shard.n_layers,
  }

  weight_files = glob.glob(str(model_path / "model*.safetensors"))

  if not weight_files:
    # Try weight for back-compat
    weight_files = glob.glob(str(model_path / "weight*.safetensors"))

  if not weight_files:
    logging.error(f"No safetensors found in {model_path}")
    raise FileNotFoundError(f"No safetensors found in {model_path}")

  weights = {}
  for wf in weight_files:
    weights.update(mx.load(wf))

  model_class, model_args_class = _get_classes(config=config)

  model_args = model_args_class.from_dict(config)
  model = model_class(model_args)

  if hasattr(model, "sanitize"):
    weights = model.sanitize(weights)

  if (quantization := config.get("quantization", None)) is not None:
    nn.quantize(
      model,
      **quantization,
      class_predicate=None,
    )

  model.load_weights(list(weights.items()), strict=True)

  if not lazy:
    mx.eval(model.parameters())

  model.eval()
  return model


async def get_repo_size(repo_id: str, revision: Optional[str] = None, allow_patterns: Optional[Union[List[str], str]] = None, repo_type: Optional[str] = None):
  it = await asyncio.to_thread(list_repo_tree, repo_id, revision=revision, repo_type=repo_type)
  files = list(filter_repo_objects(it, allow_patterns=allow_patterns, key=lambda f: f.path))
  return sum(file.size for file in files if file.size is not None)

async def monitor_progress(dir, total_size, print_progress=False, on_progress: Callable[[int, int], None] = None):
    while True:
        await asyncio.sleep(0.1)
        current_size = sum(os.path.getsize(os.path.join(root, file))
                           for root, _, files in os.walk(dir)
                           for file in files)
        progress = min(current_size / total_size * 100, 100)
        if print_progress:
          print(f"\rProgress: {progress:.2f}% ({current_size}/{total_size} bytes)", end="", flush=True)
        if on_progress:
          on_progress(current_size, total_size)
        if progress >= 100:
          if print_progress:
            print("\nDownload complete!")
          break

async def download_repo(repo_id: str, revision: Optional[str] = None, allow_patterns: Optional[Union[List[str], str]] = None, repo_type: Optional[str] = None):
  # Use snapshot_download in a separate thread to not block the event loop
  return await asyncio.to_thread(snapshot_download, repo_id=repo_id, revision=revision, allow_patterns=allow_patterns, repo_type=repo_type)

async def download_async_with_progress(repo_id: str, revision: Optional[str] = None, allow_patterns: Optional[Union[List[str], str]] = None, repo_type: Optional[str] = None, on_progress: Callable[[int, int], None] = None):
  storage_folder = os.path.join(HF_HUB_CACHE, repo_folder_name(repo_id=repo_id, repo_type="model"))
  # os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
  # os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

  total_size = await get_repo_size(repo_id)

  # Create tasks for download and progress checking
  download_task = asyncio.create_task(download_repo(repo_id, revision=revision, allow_patterns=allow_patterns, repo_type=repo_type))
  progress_task = asyncio.create_task(monitor_progress(storage_folder, total_size, on_progress=on_progress))

  # Wait for both tasks to complete
  result = await asyncio.gather(download_task, progress_task)
  return result[0]  # Return the result from download_task


async def get_model_path(path_or_hf_repo: str, revision: Optional[str] = None, on_download_progress: Callable[[int, int], None] = None) -> Path:
  """
  Ensures the model is available locally. If the path does not exist locally,
  it is downloaded from the Hugging Face Hub.

  Args:
   path_or_hf_repo (str): The local path or Hugging Face repository ID of the model.
   revision (str, optional): A revision id which can be a branch name, a tag, or a commit hash.

  Returns:
   Path: The path to the model.
  """
  model_path = Path(path_or_hf_repo)
  if not model_path.exists():
    try:
      model_path = Path(
        await download_async_with_progress(
          repo_id=path_or_hf_repo,
          revision=revision,
          allow_patterns=[
            "*.json",
            "*.safetensors",
            "*.py",
            "tokenizer.model",
            "*.tiktoken",
            "*.txt",
          ],
          on_progress=on_download_progress,
        )
      )
    except RepositoryNotFoundError:
      raise ModelNotFoundError(
        f"Model not found for path or HF repo: {path_or_hf_repo}.\n"
        "Please make sure you specified the local path or Hugging Face"
        " repo id correctly.\nIf you are trying to access a private or"
        " gated Hugging Face repo, make sure you are authenticated:\n"
        "https://huggingface.co/docs/huggingface_hub/en/guides/cli#huggingface-cli-login"
      ) from None
  return model_path


async def load_shard(
  path_or_hf_repo: str,
  shard: Shard,
  tokenizer_config={},
  model_config={},
  adapter_path: Optional[str] = None,
  lazy: bool = False,
  on_download_progress: Callable[[int, int], None] = None,
) -> Tuple[nn.Module, TokenizerWrapper]:
  """
  Load the model and tokenizer from a given path or a huggingface repository.

  Args:
   path_or_hf_repo (Path): The path or the huggingface repository to load the model from.
   tokenizer_config (dict, optional): Configuration parameters specifically for the tokenizer.
    Defaults to an empty dictionary.
   model_config(dict, optional): Configuration parameters specifically for the model.
    Defaults to an empty dictionary.
   adapter_path (str, optional): Path to the LoRA adapters. If provided, applies LoRA layers
    to the model. Default: ``None``.
   lazy (bool): If False eval the model parameters to make sure they are
    loaded in memory before returning, otherwise they will be loaded
    when needed. Default: ``False``
  Returns:
   Tuple[nn.Module, TokenizerWrapper]: A tuple containing the loaded model and tokenizer.

  Raises:
   FileNotFoundError: If config file or safetensors are not found.
   ValueError: If model class or args class are not found.
  """
  model_path = await get_model_path(path_or_hf_repo, on_download_progress=on_download_progress)

  model = load_model_shard(model_path, shard, lazy, model_config)
  if adapter_path is not None:
    model = apply_lora_layers(model, adapter_path)
    model.eval()

  # TODO: figure out a generic solution
  if model.model_type == "llava":
    processor = AutoProcessor.from_pretrained(model_path)
    processor.eos_token_id = processor.tokenizer.eos_token_id
    processor.encode = processor.tokenizer.encode
    return model, processor
  else:
    tokenizer = load_tokenizer(model_path, tokenizer_config)
    return model, tokenizer

async def get_image_from_str(_image_str: str):
    image_str = _image_str.strip()

    if image_str.startswith("http"):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_str, timeout=10) as response:
                content = await response.read()
                return Image.open(BytesIO(content)).convert("RGB")
    elif image_str.startswith("data:image/"):
        # Extract the image format and base64 data
        format_prefix, base64_data = image_str.split(";base64,")
        image_format = format_prefix.split("/")[1].lower()
        if DEBUG >= 2: print(f"{image_str=} {image_format=}")
        imgdata = base64.b64decode(base64_data)
        img = Image.open(BytesIO(imgdata))

        # Convert to RGB if not already
        if img.mode != "RGB":
            img = img.convert("RGB")

        return img
    else:
        raise ValueError("Invalid image_str format. Must be a URL or a base64 encoded image.")
