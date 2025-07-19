# 🚀 Exo Installation Guide for macOS with Apple Silicon (MLX)

This guide provides step-by-step instructions for installing exo with MLX support on macOS with Apple Silicon.

## 📋 Prerequisites

### System Requirements
- **macOS** with Apple Silicon (M1/M2/M3/M4 chips)
- **Python 3.12 or higher** (tested with Python 3.13.5)
- **Git** for cloning the repository
- **Homebrew** package manager
- **Sufficient RAM** to run the models you want to use

### Pre-installation Checks

1. **Check Python version:**
   ```bash
   python3 --version
   # Should output: Python 3.12.0 or higher
   ```

2. **Check system architecture:**
   ```bash
   uname -m
   # Should output: arm64 (for Apple Silicon)
   ```

3. **Check macOS version:**
   ```bash
   sw_vers -productVersion
   # Recommended: macOS Sequoia (15.x) or later for best performance
   ```

### Required System Dependencies

Install these with Homebrew before proceeding:
```bash
# Install cmake, protobuf, and sentencepiece
brew install cmake protobuf sentencepiece

# Verify installations
cmake --version
protoc --version
```

⚠️ **Important**: These system dependencies are required for building certain Python packages like sentencepiece.

## 🛠️ Installation Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/exo-explore/exo.git
cd exo
```

### Step 2: Create and Prepare Virtual Environment
```bash
# Create a Python virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# CRITICAL: Upgrade pip, setuptools, and wheel first
pip install --upgrade pip setuptools wheel
```

⚠️ **Note**: Upgrading pip and setuptools is crucial for compatibility with Python 3.13+

### Step 3: Handle Python 3.13 Compatibility (if needed)

If you're using Python 3.13, you may need to modify `setup.py` for compatibility:

1. **Update numpy version** (if errors occur):
   ```bash
   # Install compatible numpy first
   pip install numpy==2.2.1
   ```

2. **Update MLX versions in setup.py**:
   - Change `mlx==0.22.0` to `mlx==0.26.5`
   - Change `mlx-lm==0.21.1` to `mlx-lm==0.22.3`

### Step 4: Install Exo with MLX Support
```bash
# Install exo in editable mode (automatically includes MLX on Apple Silicon)
pip install -e .
```

This will:
- Automatically detect Apple Silicon and install MLX
- Install all base dependencies including:
  - aiohttp for web server
  - grpcio for node communication
  - transformers for model handling
  - tinygrad as alternate inference engine
  - MLX and mlx-lm for Apple Silicon optimization
  - All other required packages

⚠️ **Troubleshooting Installation Issues:**

1. **If numpy compilation fails**: Install pre-compiled wheel
   ```bash
   pip install numpy==2.2.1  # or latest version
   ```

2. **If sentencepiece fails**: Ensure brew dependencies are installed
   ```bash
   brew install cmake protobuf sentencepiece
   ```

3. **If MLX version conflicts**: Check available versions
   ```bash
   pip index versions mlx
   pip index versions mlx-lm
   ```

### Step 5: Handle System MLX Conflicts (if needed)

If you have MLX installed via Homebrew, it may conflict with the virtual environment's MLX:
```bash
# Check if MLX is installed via Homebrew
brew list | grep mlx

# If found, unlink it temporarily
brew unlink mlx
```

This prevents library loading conflicts between system and venv MLX installations.

### Step 6: Optimize MLX Performance (Highly Recommended)
```bash
# Make the script executable if needed
chmod +x configure_mlx.sh

# Run the MLX configuration script
./configure_mlx.sh
```

This script:
- Calculates optimal GPU memory limits based on your system RAM
- Sets `iogpu.wired_limit_mb` to 80% of RAM or (RAM - 5GB), whichever is higher
- Sets `iogpu.wired_lwm_mb` to 70% of RAM or (RAM - 8GB), whichever is higher
- May require sudo password
- Improves performance significantly on Apple Silicon

### Step 7: Verify Installation
```bash
# Check if exo command is available
which exo
# Should output: /Users/[username]/exo/.venv/bin/exo

# Test the installation
exo --help

# Check installed packages
pip list | grep -E "mlx|exo|tinygrad"
# Should show:
# exo                0.0.1
# mlx                0.26.5
# mlx-lm             0.22.3
# mlx-metal          0.26.5
# tinygrad           0.10.0
```

## 🚀 Running Exo

### Basic Usage
```bash
# Start exo node (will auto-discover other nodes)
exo

# Run a specific model directly
exo run llama-3.2-3b --prompt "What is the meaning of exo?"

# Specify inference engine explicitly (optional, MLX is default on Apple Silicon)
exo --inference-engine mlx
```

### Web Interface
Once running, exo provides:
- WebUI at: http://localhost:52415
- ChatGPT-compatible API at: http://localhost:52415/v1/chat/completions

## 📁 Model Storage
- Default location: `~/.cache/exo/downloads`
- To change: Set `EXO_HOME` environment variable
  ```bash
  export EXO_HOME=/path/to/your/models
  ```

## 🔧 Troubleshooting

### SSL Certificate Issues
If you encounter SSL errors when downloading models:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

### Memory Issues
- Ensure you have enough RAM for the model you're trying to run
- Check Activity Monitor for memory usage
- Try smaller models if encountering out-of-memory errors

### Performance Optimization
1. Update to latest macOS Sequoia
2. Close unnecessary applications
3. Run `./configure_mlx.sh` if not already done
4. Use `DEBUG=9 exo` for detailed debug logs

## 🔄 Updating Exo

To update to the latest version:
```bash
cd exo
git pull
pip install -e . --upgrade
```

## 🗑️ Uninstallation

To completely remove exo:
```bash
# Deactivate virtual environment if active
deactivate

# Remove the repository
cd ..
rm -rf exo

# Remove cached models (optional)
rm -rf ~/.cache/exo
```

## ⚠️ Common Warnings (Can Be Ignored)

1. **Protobuf version warning:**
   ```
   UserWarning: Protobuf gencode version 5.27.2 is older than the runtime version 5.28.1
   ```
   This is harmless and can be ignored.

2. **PyTorch/TensorFlow warning:**
   ```
   None of PyTorch, TensorFlow >= 2.0, or Flax have been found
   ```
   This is expected as exo uses MLX and tinygrad, not PyTorch.

## 🚀 Quick Start Example

After installation, test exo with a small model:

```bash
# Start exo node (will auto-discover other nodes)
exo

# Or run a model directly
exo run llama-3.2-3b --prompt "What is the meaning of exo?"

# Check the web interface
open http://localhost:52415
```

## 📝 Notes

- MLX is automatically installed on Apple Silicon Macs
- The inference engine will default to MLX on macOS ARM64
- For multi-device setups, ensure all devices are on the same network
- Models are automatically downloaded from Hugging Face when first requested
- Model files are stored in `~/.cache/exo/downloads` by default

## 🆘 Getting Help

- Discord: https://discord.gg/EUnjGpsmWw
- GitHub Issues: https://github.com/exo-explore/exo/issues
- Documentation: Check the main README.md for more details

## 📦 Installation Script

For automated installation, save this as `install_exo.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Installing exo with MLX support..."

# Check Python version
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
    echo "❌ Python 3.12 or higher is required"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install cmake protobuf sentencepiece || true

# Clone repo
if [ ! -d "exo" ]; then
    git clone https://github.com/exo-explore/exo.git
fi
cd exo

# Create venv
echo "🐍 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install numpy first if Python 3.13+
if python3 -c 'import sys; exit(0 if sys.version_info >= (3,13) else 1)' 2>/dev/null; then
    echo "📊 Installing numpy for Python 3.13+..."
    pip install numpy==2.2.1
fi

# Unlink system MLX if present
if brew list | grep -q mlx; then
    echo "🔗 Unlinking system MLX..."
    brew unlink mlx || true
fi

# Install exo
echo "📥 Installing exo..."
pip install -e .

# Run MLX optimization
echo "⚡ Optimizing MLX performance..."
chmod +x configure_mlx.sh
./configure_mlx.sh

echo "✅ Installation complete!"
echo "🎯 Run 'source .venv/bin/activate && exo --help' to get started"
```