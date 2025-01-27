from exo.download.new_shard_download import download_shard, NewShardDownloader
from exo.inference.shard import Shard
from pathlib import Path
import asyncio

async def test_new_shard_download():
  shard_downloader = NewShardDownloader()
  shard_downloader.on_progress.register("test").on_next(lambda shard, event: print(shard, event))
  await shard_downloader.ensure_shard(Shard(model_id="llama-3.2-1b", start_layer=0, end_layer=0, n_layers=16), "MLXDynamicShardInferenceEngine")
  download_statuses = await shard_downloader.get_shard_download_status("MLXDynamicShardInferenceEngine")
  print({k: v for k, v in download_statuses if v.downloaded_bytes > 0})

if __name__ == "__main__":
  asyncio.run(test_new_shard_download())

