#!/bin/zsh
# 🚀 ShoemoneyAI Cluster - Universal Exo Installation Script
# This script sets up exo on any Unix-like system for distributed AI inference
# Designed to work across multiple nodes in your cluster
deactivate
source /Users/shoemoney/exo/venv/bin/activate
set -e  # Exit on error

# 🎨 Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 📍 Configuration
INSTALL_DIR="${INSTALL_DIR:-$HOME/exo}"
PYTHON_VERSION="3.11"  # 3.11 for better compatibility than 3.13

# 🌐 Network configuration - use hostname for cluster access
HOSTNAME="$(hostname -s)"
NODE_NAME="${NODE_NAME:-$(hostname -s)}"
REPO_URL="https://github.com/exo-explore/exo.git"
BRANCH="main"

# 🔍 System detection
detect_system() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            SYSTEM="debian"
            DISTRO=$(lsb_release -cs 2>/dev/null || echo "unknown")
        elif [ -f /etc/redhat-release ]; then
            SYSTEM="redhat"
            DISTRO=$(cat /etc/redhat-release)
        elif [ -f /etc/arch-release ]; then
            SYSTEM="arch"
            DISTRO="Arch Linux"
        else
            SYSTEM="linux"
            DISTRO="Unknown Linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM="macos"
        DISTRO="macOS $(sw_vers -productVersion)"
    else
        SYSTEM="unknown"
        DISTRO="Unknown"
    fi
    
    # Detect architecture
    ARCH=$(uname -m)
    
    echo -e "${CYAN}🖥️  System: ${DISTRO} (${ARCH})${NC}"
}

# 📦 Install system dependencies
install_dependencies() {
    echo -e "${BLUE}📦 Installing system dependencies...${NC}"
    
    case $SYSTEM in
        debian)
            echo -e "${YELLOW}Updating package lists...${NC}"
            sudo apt-get update
            
            echo -e "${YELLOW}Installing required packages...${NC}"
            sudo apt-get install -y \
                build-essential \
                python3-pip \
                python3-dev \
                python3-venv \
                git \
                cmake \
                protobuf-compiler \
                curl \
                wget \
                screen \
                tmux \
                htop \
                libssl-dev \
                libffi-dev \
                libbz2-dev \
                libreadline-dev \
                libsqlite3-dev \
                libncurses5-dev \
                libncursesw5-dev \
                xz-utils \
                tk-dev \
                libxml2-dev \
                libxmlsec1-dev \
                liblzma-dev \
                libopenblas-dev \
                liblapack-dev
            ;;
            
        redhat)
            echo -e "${YELLOW}Installing required packages...${NC}"
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                python3 \
                python3-pip \
                python3-devel \
                git \
                cmake \
                protobuf-compiler \
                screen \
                tmux \
                htop \
                openssl-devel \
                libffi-devel \
                bzip2-devel \
                readline-devel \
                sqlite-devel \
                ncurses-devel \
                xz-devel \
                tk-devel \
                libxml2-devel \
                xmlsec1-devel \
                openblas-devel \
                lapack-devel
            ;;
            
        arch)
            echo -e "${YELLOW}Installing required packages...${NC}"
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm \
                base-devel \
                python \
                python-pip \
                git \
                cmake \
                protobuf \
                screen \
                tmux \
                htop \
                openssl \
                libffi \
                bzip2 \
                readline \
                sqlite \
                ncurses \
                xz \
                tk \
                libxml2 \
                xmlsec \
                openblas \
                lapack
            ;;
            
        macos)
            # Check if Homebrew is installed
            if ! command -v brew &> /dev/null; then
                echo -e "${YELLOW}Installing Homebrew...${NC}"
                /bin/zsh -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            echo -e "${YELLOW}Installing required packages...${NC}"
            brew install \
                python@${PYTHON_VERSION} \
                cmake \
                protobuf \
                git \
                screen \
                tmux \
                htop \
                openblas \
                lapack \
                sentencepiece \
                grpc
            ;;
    esac
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# 🐍 Setup Python environment
setup_python() {
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    
    # Install pyenv for consistent Python version
    if ! command -v pyenv &> /dev/null; then
        echo -e "${YELLOW}Installing pyenv...${NC}"
        curl https://pyenv.run | zsh
        
        # Add pyenv to PATH
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        
        # Add to shell profile
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
        echo 'eval "$(pyenv init -)"' >> ~/.zshrc
    fi
    
    # Install Python version
    echo -e "${YELLOW}Installing Python ${PYTHON_VERSION}...${NC}"
    pyenv install -s ${PYTHON_VERSION}
    pyenv global ${PYTHON_VERSION}
    
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} ready${NC}"
}

# 📥 Clone and setup exo
setup_exo() {
    echo -e "${BLUE}📥 Setting up exo...${NC}"
    
    # Clone repository
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}Exo directory exists. Updating...${NC}"
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/$BRANCH
    else
        echo -e "${YELLOW}Cloning exo repository...${NC}"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
        git checkout $BRANCH
    fi
    
    # Create virtual environment
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv .venv
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install exo based on system
    echo -e "${YELLOW}Installing exo...${NC}"
    if [[ "$SYSTEM" == "macos" ]] && [[ "$ARCH" == "arm64" ]]; then
        # Apple Silicon - install with MLX
        pip install -e ".[mlx]"
    else
        # Other systems - basic install
        pip install -e .
        
        # Install tinygrad for non-Apple systems
        pip install tinygrad
    fi
    
    # Fix common issues
    echo -e "${YELLOW}Applying fixes...${NC}"
    
    # Update numpy for Python 3.11+ compatibility
    pip install --upgrade numpy
    
    # Fix protobuf issues
    pip install --upgrade protobuf grpcio grpcio-tools
    
    # Regenerate protobuf files
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --pyi_out=. exo/networking/grpc/node_service.proto || true
    
    echo -e "${GREEN}✅ Exo installed successfully${NC}"
}

# 🔧 Configure the node
configure_node() {
    echo -e "${BLUE}🔧 Configuring node...${NC}"
    
    # Copy screen configuration
    cp .screenrc ~/.screenrc
    echo -e "${GREEN}✅ Screen configuration installed${NC}"
    
    # Create systemd service (Linux only)
    if [[ "$SYSTEM" == "debian" ]] || [[ "$SYSTEM" == "redhat" ]] || [[ "$SYSTEM" == "arch" ]]; then
        echo -e "${YELLOW}Creating systemd service...${NC}"
        
        sudo tee /etc/systemd/system/exo-node.service > /dev/null << EOF
[Unit]
Description=Exo AI Cluster Node
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/.venv/bin/python -m exo.main --node-id $NODE_NAME
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        echo -e "${GREEN}✅ Systemd service created (exo-node.service)${NC}"
    fi
    
    # Create convenience scripts
    echo -e "${YELLOW}Creating helper scripts...${NC}"
    
    # Start script
    cat > "$INSTALL_DIR/start-node.sh" << 'EOF'
#!/bin/zsh
cd "$(dirname "$0")"
source .venv/bin/activate
exec python -m exo.main "$@"
EOF
    chmod +x "$INSTALL_DIR/start-node.sh"
    
    # Update script
    cat > "$INSTALL_DIR/update-node.sh" << 'EOF'
#!/bin/zsh
cd "$(dirname "$0")"
git pull
source .venv/bin/activate
pip install -e . --upgrade
echo "✅ Node updated!"
EOF
    chmod +x "$INSTALL_DIR/update-node.sh"
    
    echo -e "${GREEN}✅ Helper scripts created${NC}"
}

# 🚀 Create cluster management scripts
create_cluster_scripts() {
    echo -e "${BLUE}🚀 Creating cluster management scripts...${NC}"
    
    # Create cluster config directory
    mkdir -p "$HOME/.exo-cluster"
    
    # Node discovery config template
    cat > "$HOME/.exo-cluster/nodes.json" << EOF
{
  "nodes": [
    {
      "id": "$NODE_NAME",
      "host": "$(hostname -I | awk '{print $1}')",
      "port": 5678
    }
  ]
}
EOF
    
    # Cluster status script
    cat > "$INSTALL_DIR/cluster-status.sh" << 'EOF'
#!/bin/zsh
# 📊 Check status of all cluster nodes

echo "🔍 Checking Exo Cluster Status..."
echo "================================="

# Local node
echo "📍 Local Node:"
if pgrep -f "python.*exo.main" > /dev/null; then
    echo "  ✅ Running (PID: $(pgrep -f "python.*exo.main"))"
else
    echo "  ❌ Not running"
fi

# Check systemd service if available
if command -v systemctl &> /dev/null && systemctl list-units --type=service | grep -q exo-node; then
    echo "  Service: $(systemctl is-active exo-node)"
fi

echo ""
echo "🌐 API Endpoints:"
echo "  Web UI: http://$HOSTNAME.local:52415"
echo "  API: http://$HOSTNAME.local:52415/v1/chat/completions"
EOF
    chmod +x "$INSTALL_DIR/cluster-status.sh"
    
    echo -e "${GREEN}✅ Cluster scripts created${NC}"
}

# 🎯 Setup profile additions
setup_profile() {
    echo -e "${BLUE}🎯 Setting up shell profile...${NC}"
    
    PROFILE_FILE="$HOME/.zshrc"
    if [[ "$SYSTEM" == "macos" ]]; then
        PROFILE_FILE="$HOME/.zshrc"
    fi
    
    # Add exo to PATH
    if ! grep -q "exo cluster" "$PROFILE_FILE"; then
        cat >> "$PROFILE_FILE" << EOF

# 🚀 Exo AI Cluster
export EXO_HOME="$INSTALL_DIR"
alias exo-start="cd \$EXO_HOME && ./start-node.sh"
alias exo-status="\$EXO_HOME/cluster-status.sh"
alias exo-update="\$EXO_HOME/update-node.sh"
alias exo-logs="journalctl -u exo-node -f"
alias exo-screen="screen -r exo-cluster"

# Quick cluster commands
alias cluster-start="cd \$EXO_HOME && ./start_cluster.sh"
alias cluster-attach="screen -r exo-cluster"
EOF
        echo -e "${GREEN}✅ Shell aliases added${NC}"
    fi
}

# 🔐 SSH key setup for cluster
setup_ssh_keys() {
    echo -e "${BLUE}🔐 Setting up SSH keys for cluster...${NC}"
    
    if [ ! -f "$HOME/.ssh/id_rsa" ]; then
        echo -e "${YELLOW}Generating SSH key...${NC}"
        ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/id_rsa" -N "" -C "exo-cluster-$NODE_NAME"
    fi
    
    echo -e "${GREEN}Your SSH public key for cluster setup:${NC}"
    echo -e "${CYAN}$(cat $HOME/.ssh/id_rsa.pub)${NC}"
    echo -e "${YELLOW}Add this key to other nodes' ~/.ssh/authorized_keys${NC}"
}

# 📊 Final setup summary
show_summary() {
    echo -e "\n${BOLD}${CYAN}🎉 Exo Installation Complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📍 Installation Directory:${NC} $INSTALL_DIR"
    echo -e "${GREEN}🐍 Python Version:${NC} $(python --version)"
    echo -e "${GREEN}💻 Node Name:${NC} $NODE_NAME"
    echo -e "${GREEN}🖥️  System:${NC} $DISTRO ($ARCH)"
    
    echo -e "\n${YELLOW}🚀 Quick Start Commands:${NC}"
    echo -e "  ${CYAN}exo-start${NC}              # Start this node"
    echo -e "  ${CYAN}exo-status${NC}             # Check node status"
    echo -e "  ${CYAN}cluster-start${NC}          # Start local cluster in screen"
    echo -e "  ${CYAN}cluster-attach${NC}         # Attach to cluster screen"
    echo -e "  ${CYAN}exo-update${NC}             # Update exo to latest"
    
    if [[ "$SYSTEM" != "macos" ]]; then
        echo -e "\n${YELLOW}🔧 Systemd Commands:${NC}"
        echo -e "  ${CYAN}sudo systemctl start exo-node${NC}    # Start service"
        echo -e "  ${CYAN}sudo systemctl enable exo-node${NC}   # Enable on boot"
        echo -e "  ${CYAN}sudo systemctl status exo-node${NC}   # Check status"
    fi
    
    echo -e "\n${YELLOW}🌐 Access Points:${NC}"
    echo -e "  ${CYAN}Web UI:${NC} http://$HOSTNAME.local:52415"
    echo -e "  ${CYAN}API:${NC} http://$HOSTNAME.local:52415/v1/chat/completions"
    
    echo -e "\n${PURPLE}📚 Next Steps:${NC}"
    echo -e "1. Source your profile: ${CYAN}source $PROFILE_FILE${NC}"
    echo -e "2. Start the node: ${CYAN}exo-start${NC}"
    echo -e "3. Copy SSH key to other nodes for clustering"
    echo -e "4. Configure firewall for ports 5678-5679, 52415"
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}Happy clustering! 🚀${NC}\n"
}

# 🎬 Main installation flow
main() {
    echo -e "${BOLD}${CYAN}🚀 ShoemoneyAI Cluster - Exo Installation${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # Detect system
    detect_system
    
    # Run installation steps
    install_dependencies
    setup_python
    setup_exo
    configure_node
    create_cluster_scripts
    setup_profile
    setup_ssh_keys
    
    # Show summary
    show_summary
}

# Run main function
main "$@"
