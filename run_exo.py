#!/usr/bin/env python3
"""
🚀 Clean launcher for exo that suppresses known warnings
"""
import warnings
import os
import sys

# 🔇 Suppress protobuf version warnings
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf.runtime_version')

# 🔇 Suppress transformers PyTorch/TensorFlow warnings
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
warnings.filterwarnings('ignore', message='None of PyTorch, TensorFlow >= 2.0, or Flax have been found')

# 🎯 Import and run exo
from exo.main import run
if __name__ == "__main__":
    run()