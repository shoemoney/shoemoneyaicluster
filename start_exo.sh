#!/bin/bash

# 🚀 ShoeMoney AI Cluster - Easy Startup Script
# This script automatically sets up and runs exo with the correct Python version

set -e

# 🎯 Color output for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 ShoeMoney AI Cluster Startup${NC}"
echo -e "${BLUE}================================${NC}"

# 📁 Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# ✅ Check for Python 3.12
if ! command -v /opt/homebrew/bin/python3.12 &> /dev/null; then
    echo -e "${RED}❌ Python 3.12 not found. Please install with: brew install python@3.12${NC}"
    exit 1
fi

# 🔧 Create or activate virtual environment
if [ ! -d "exo_venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment with Python 3.12...${NC}"
    /opt/homebrew/bin/python3.12 -m venv exo_venv
    
    echo -e "${YELLOW}⚡ Installing dependencies...${NC}"
    source exo_venv/bin/activate
    pip install -e .
else
    echo -e "${GREEN}✅ Virtual environment found, activating...${NC}"
    source exo_venv/bin/activate
fi

# 🎯 Apple Silicon optimization
if [[ $(uname -m) == "arm64" ]]; then
    echo -e "${BLUE}🍎 Optimizing for Apple Silicon...${NC}"
    ./configure_mlx.sh
fi

# 🎊 Success message
echo -e "${GREEN}✅ Setup complete! Starting exo...${NC}"
echo -e "${CYAN}💡 Access the web UI at: http://localhost:52415${NC}"
echo -e "${CYAN}📡 API endpoint at: http://localhost:52415/v1/chat/completions${NC}"
echo ""

# 🚀 Launch exo with provided arguments or default
if [ $# -eq 0 ]; then
    echo -e "${PURPLE}🎯 Starting exo in cluster mode...${NC}"
    exo
else
    echo -e "${PURPLE}🎯 Starting exo with arguments: $@${NC}"
    exo "$@"
fi