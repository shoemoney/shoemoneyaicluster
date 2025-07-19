#!/bin/bash
# 🎯 Quick cluster starter - Launch multiple exo nodes easily

set -e

# 🎨 Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 📍 Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLUSTER_SCRIPT="$SCRIPT_DIR/clusterexo.sh"

# 🌐 Network configuration - use hostname for cluster access
HOSTNAME="$(hostname -s)"

# 📺 Function to start nodes in screen (best for remote sessions)
start_in_screen() {
    local num_nodes="${1:-2}"
    local node_host_arg=""
    [ -n "$NODE_HOST" ] && node_host_arg="--node-host $NODE_HOST"
    
    echo -e "${CYAN}🚀 Starting ${num_nodes} node cluster in screen...${NC}"
    
    # Check if screen is installed
    if ! command -v screen &> /dev/null; then
        echo -e "${YELLOW}⚠️  screen not found! Install with:${NC}"
        echo -e "  ${GREEN}macOS:${NC} brew install screen"
        echo -e "  ${GREEN}Ubuntu/Debian:${NC} sudo apt-get install screen"
        echo -e "  ${GREEN}CentOS/RHEL:${NC} sudo yum install screen"
        exit 1
    fi
    
    # Kill existing exo-cluster session if it exists
    screen -S exo-cluster -X quit 2>/dev/null || true
    
    # Start main node in new screen session
    screen -dmS exo-cluster -t main bash -c "cd $SCRIPT_DIR && $CLUSTER_SCRIPT --node-id main --wait-peers $((num_nodes-1)) $node_host_arg; exec bash"
    
    # Start worker nodes in new windows
    for i in $(seq 1 $((num_nodes-1))); do
        screen -S exo-cluster -X screen -t "worker$i" bash -c "cd $SCRIPT_DIR && $CLUSTER_SCRIPT --node-id worker$i $node_host_arg; exec bash"
    done
    
    echo -e "${GREEN}✅ Cluster started in screen session 'exo-cluster'${NC}"
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  ${YELLOW}screen -r exo-cluster${NC}        # Attach to session"
    echo -e "  ${YELLOW}screen -ls${NC}                   # List sessions"
    echo -e "  ${YELLOW}Ctrl+A, D${NC}                    # Detach from session"
    echo -e "  ${YELLOW}Ctrl+A, N${NC}                    # Next window"
    echo -e "  ${YELLOW}Ctrl+A, P${NC}                    # Previous window"
    echo -e "  ${YELLOW}Ctrl+A, 0-9${NC}                  # Switch to window by number"
    echo -e "  ${YELLOW}Ctrl+A, "${NC}                    # List all windows"
    echo -e "  ${YELLOW}Ctrl+A, K${NC}                    # Kill current window"
    echo ""
    echo -e "${CYAN}🌐 Web Interface:${NC} http://$HOSTNAME.local:52415"
    echo -e "${CYAN}🔌 API Endpoint:${NC} http://$HOSTNAME.local:52415/v1/chat/completions"
    
    # Ask if user wants to attach
    read -p "$(echo -e ${YELLOW}Attach to screen session now? [Y/n]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        screen -r exo-cluster
    fi
}

# 🚀 Function to start nodes in tmux
start_in_tmux() {
    local num_nodes="${1:-2}"
    local node_host_arg=""
    [ -n "$NODE_HOST" ] && node_host_arg="--node-host $NODE_HOST"
    
    echo -e "${CYAN}🚀 Starting ${num_nodes} node cluster in tmux...${NC}"
    
    # Check if tmux is installed
    if ! command -v tmux &> /dev/null; then
        echo -e "${YELLOW}⚠️  tmux not found! Install with: brew install tmux${NC}"
        exit 1
    fi
    
    # Create new tmux session
    tmux new-session -d -s exo-cluster
    
    # Start main node
    tmux send-keys -t exo-cluster "$CLUSTER_SCRIPT --node-id main --wait-peers $((num_nodes-1)) $node_host_arg" C-m
    
    # Start worker nodes
    for i in $(seq 1 $((num_nodes-1))); do
        tmux new-window -t exo-cluster -n "worker$i"
        tmux send-keys -t exo-cluster:$i "$CLUSTER_SCRIPT --node-id worker$i $node_host_arg" C-m
    done
    
    echo -e "${GREEN}✅ Cluster started in tmux session 'exo-cluster'${NC}"
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  ${YELLOW}tmux attach -t exo-cluster${NC}  # Attach to session"
    echo -e "  ${YELLOW}tmux ls${NC}                     # List sessions"
    echo -e "  ${YELLOW}Ctrl+B, D${NC}                   # Detach from session"
    echo -e "  ${YELLOW}Ctrl+B, 0-9${NC}                 # Switch windows"
    
    # Attach to session
    tmux attach -t exo-cluster
}

# 🖥️ Function to start nodes in separate terminals (macOS)
start_in_terminals() {
    local num_nodes="${1:-2}"
    local node_host_arg=""
    [ -n "$NODE_HOST" ] && node_host_arg="--node-host $NODE_HOST"
    
    echo -e "${CYAN}🚀 Starting ${num_nodes} node cluster in separate terminals...${NC}"
    
    # Start main node
    osascript -e "tell app \"Terminal\" to do script \"cd $SCRIPT_DIR && $CLUSTER_SCRIPT --node-id main --wait-peers $((num_nodes-1)) $node_host_arg\""
    
    # Start worker nodes
    for i in $(seq 1 $((num_nodes-1))); do
        sleep 1
        osascript -e "tell app \"Terminal\" to do script \"cd $SCRIPT_DIR && $CLUSTER_SCRIPT --node-id worker$i $node_host_arg\""
    done
    
    echo -e "${GREEN}✅ Cluster nodes starting in separate Terminal windows${NC}"
}

# 📋 Show help
show_help() {
    cat << EOF
${CYAN}🎯 ExoCluster Quick Starter${NC}

${YELLOW}Usage:${NC} $0 [NODES] [MODE] [OPTIONS]

${YELLOW}Arguments:${NC}
  NODES   Number of nodes to start (default: 2)
  MODE    Launch mode: screen, tmux, terminal (default: screen)

${YELLOW}Options:${NC}
  --node-host HOST    Host binding for all nodes (default: 0.0.0.0)

${YELLOW}Examples:${NC}
  $0                                      # Start 2 nodes in screen
  $0 3                                    # Start 3 nodes in screen
  $0 4 tmux                               # Start 4 nodes in tmux
  $0 2 terminal                           # Start 2 nodes in separate terminals
  $0 3 screen --node-host 192.168.1.11   # 3 nodes with specific host binding

${BLUE}Tips:${NC}
  - Screen mode is best for remote sessions
  - Tmux mode for local development
  - Terminal mode opens separate windows (macOS only)
  - Access web UI at http://$HOSTNAME.local:52415

${GREEN}Screen Commands:${NC}
  Ctrl+A, N       Next window
  Ctrl+A, P       Previous window
  Ctrl+A, D       Detach session
  Ctrl+A, "       List windows

EOF
}

# 🎬 Main
main() {
    local num_nodes="${1:-2}"
    local mode="${2:-screen}"
    
    # Parse remaining arguments for options
    shift 2 2>/dev/null || true  # Remove first two args safely
    while [[ $# -gt 0 ]]; do
        case $1 in
            --node-host)
                NODE_HOST="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${YELLOW}Unknown option: $1${NC}"
                shift
                ;;
        esac
    done
    
    if [[ "$num_nodes" == "-h" ]] || [[ "$num_nodes" == "--help" ]]; then
        show_help
        exit 0
    fi
    
    case "$mode" in
        screen)
            start_in_screen "$num_nodes"
            ;;
        tmux)
            start_in_tmux "$num_nodes"
            ;;
        terminal)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                start_in_terminals "$num_nodes"
            else
                echo -e "${YELLOW}Terminal mode only supported on macOS. Using screen instead.${NC}"
                start_in_screen "$num_nodes"
            fi
            ;;
        *)
            echo -e "${YELLOW}Unknown mode: $mode. Using screen.${NC}"
            start_in_screen "$num_nodes"
            ;;
    esac
}

main "$@"