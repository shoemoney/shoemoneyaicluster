#!/bin/bash
# 🚀 Cluster launcher for exo - Run your own AI cluster at home!
# This script helps you quickly start exo nodes for a distributed AI cluster

set -e  # Exit on error

# 🎨 Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 📍 Default values
DEFAULT_NODE_ID="$(hostname -s)"
DEFAULT_LISTEN_PORT=5678
DEFAULT_BROADCAST_PORT=5679
DEFAULT_CHATGPT_PORT=52415
DEFAULT_DISCOVERY="udp"
DEFAULT_INFERENCE_ENGINE="mlx"

# 🌐 Network configuration - use hostname for cluster access
HOSTNAME="$(hostname -s)"
LOCAL_IP="$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' || echo 'localhost')"

# 🛠️ Configuration
VENV_PATH=".venv"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 📋 Function to display help
show_help() {
    cat << EOF
${CYAN}🚀 ExoCluster - Distributed AI Cluster Launcher${NC}

${YELLOW}Usage:${NC} $0 [OPTIONS]

${YELLOW}Options:${NC}
  ${GREEN}-h, --help${NC}              Show this help message
  ${GREEN}-n, --node-id${NC}           Node ID (default: hostname)
  ${GREEN}-d, --discovery${NC}         Discovery module: udp, manual, tailscale (default: udp)
  ${GREEN}-e, --engine${NC}            Inference engine: mlx, tinygrad, dummy (default: mlx)
  ${GREEN}-m, --model${NC}             Default model to load
  ${GREEN}-w, --wait-peers${NC}        Number of peers to wait for before starting
  ${GREEN}--headless${NC}              Run without TUI (terminal UI)
  ${GREEN}--api-port${NC}              ChatGPT API port (default: 52415)
  ${GREEN}--listen-port${NC}           Discovery listen port (default: 5678)
  ${GREEN}--broadcast-port${NC}        Discovery broadcast port (default: 5679)
  ${GREEN}--manual-config${NC}         Path to manual discovery config JSON
  ${GREEN}--run${NC}                   Run a model directly with a prompt
  ${GREEN}--debug${NC}                 Enable debug output

${YELLOW}Examples:${NC}
  # 🎯 Start a single node
  $0

  # 🌐 Start a node and wait for 2 peers
  $0 --wait-peers 2

  # 🤖 Start with a specific model
  $0 --model llama-3.2-3b

  # 🔧 Manual discovery with config file
  $0 --discovery manual --manual-config network_config.json

  # 💬 Run a model directly
  $0 --run --model llama-3.2-3b

${YELLOW}Multi-Node Setup:${NC}
  # Terminal 1 (Main node):
  $0 --node-id main --wait-peers 1

  # Terminal 2 (Worker node):
  $0 --node-id worker1

${PURPLE}Web Interface:${NC} http://${HOSTNAME}.local:${DEFAULT_CHATGPT_PORT}
${PURPLE}API Endpoint:${NC}  http://${HOSTNAME}.local:${DEFAULT_CHATGPT_PORT}/v1/chat/completions

EOF
}

# 🔍 Function to check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Virtual environment not found!${NC}"
        echo -e "${YELLOW}Please run the installation first:${NC}"
        echo -e "  python3 -m venv $VENV_PATH"
        echo -e "  source $VENV_PATH/bin/activate"
        echo -e "  pip install -e ."
        exit 1
    fi
}

# 🚀 Function to start exo
start_exo() {
    local node_id="${NODE_ID:-$DEFAULT_NODE_ID}"
    local discovery="${DISCOVERY:-$DEFAULT_DISCOVERY}"
    local engine="${ENGINE:-$DEFAULT_INFERENCE_ENGINE}"
    local api_port="${API_PORT:-$DEFAULT_CHATGPT_PORT}"
    local listen_port="${LISTEN_PORT:-$DEFAULT_LISTEN_PORT}"
    local broadcast_port="${BROADCAST_PORT:-$DEFAULT_BROADCAST_PORT}"
    
    echo -e "${CYAN}🚀 Starting ExoCluster Node${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📍 Node ID:${NC} $node_id"
    echo -e "${GREEN}🔍 Discovery:${NC} $discovery"
    echo -e "${GREEN}⚙️  Engine:${NC} $engine"
    echo -e "${GREEN}🌐 API Port:${NC} $api_port"
    echo -e "${GREEN}📡 Listen Port:${NC} $listen_port"
    echo -e "${GREEN}📢 Broadcast Port:${NC} $broadcast_port"
    
    # Build command
    local cmd="python -m exo.main"
    cmd="$cmd --node-id $node_id"
    cmd="$cmd --discovery-module $discovery"
    cmd="$cmd --inference-engine $engine"
    cmd="$cmd --chatgpt-api-port $api_port"
    cmd="$cmd --listen-port $listen_port"
    cmd="$cmd --broadcast-port $broadcast_port"
    
    # Add optional parameters
    [ -n "$MODEL" ] && cmd="$cmd --default-model $MODEL" && echo -e "${GREEN}🤖 Model:${NC} $MODEL"
    [ -n "$WAIT_PEERS" ] && cmd="$cmd --wait-for-peers $WAIT_PEERS" && echo -e "${GREEN}👥 Wait for peers:${NC} $WAIT_PEERS"
    [ -n "$MANUAL_CONFIG" ] && cmd="$cmd --discovery-config-path $MANUAL_CONFIG" && echo -e "${GREEN}📄 Config:${NC} $MANUAL_CONFIG"
    [ "$HEADLESS" = true ] && cmd="$cmd --disable-tui"
    [ "$RUN_MODE" = true ] && cmd="$cmd run" && echo -e "${GREEN}▶️  Mode:${NC} Direct run"
    [ "$DEBUG" = true ] && export DEBUG=9 && echo -e "${GREEN}🐛 Debug:${NC} Enabled"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🌟 Web Interface:${NC} http://$HOSTNAME.local:$api_port"
    echo -e "${YELLOW}🔌 API Endpoint:${NC} http://$HOSTNAME.local:$api_port/v1/chat/completions"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Activate virtual environment and run
    source "$VENV_PATH/bin/activate"
    exec $cmd
}

# 📊 Function to show cluster status
show_status() {
    echo -e "${CYAN}📊 ExoCluster Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check for running exo processes
    local exo_procs=$(ps aux | grep "python.*exo.main" | grep -v grep || true)
    
    if [ -z "$exo_procs" ]; then
        echo -e "${YELLOW}No exo nodes currently running${NC}"
    else
        echo -e "${GREEN}Running exo nodes:${NC}"
        echo "$exo_procs" | while read line; do
            local pid=$(echo $line | awk '{print $2}')
            local node_info=$(echo $line | grep -oE "\-\-node\-id [^ ]+" || echo "--node-id default")
            echo -e "  ${GREEN}✓${NC} PID: $pid, $node_info"
        done
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 🎯 Main script logic
main() {
    cd "$SCRIPT_DIR"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--node-id)
                NODE_ID="$2"
                shift 2
                ;;
            -d|--discovery)
                DISCOVERY="$2"
                shift 2
                ;;
            -e|--engine)
                ENGINE="$2"
                shift 2
                ;;
            -m|--model)
                MODEL="$2"
                shift 2
                ;;
            -w|--wait-peers)
                WAIT_PEERS="$2"
                shift 2
                ;;
            --headless)
                HEADLESS=true
                shift
                ;;
            --api-port)
                API_PORT="$2"
                shift 2
                ;;
            --listen-port)
                LISTEN_PORT="$2"
                shift 2
                ;;
            --broadcast-port)
                BROADCAST_PORT="$2"
                shift 2
                ;;
            --manual-config)
                MANUAL_CONFIG="$2"
                shift 2
                ;;
            --run)
                RUN_MODE=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --status)
                show_status
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Check virtual environment
    check_venv
    
    # Start exo
    start_exo
}

# 🎬 Run main function
main "$@"