#!/bin/bash

# MariaDB Setup Script for Exo Cluster
# Configures MariaDB server and creates the necessary database and user

set -e

echo "🚀 MariaDB Setup for Exo Cluster"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}⚠️  This script should not be run as root${NC}"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Function to prompt for input with default
prompt_input() {
    local prompt="$1"
    local default="$2"
    local value
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value=${value:-$default}
    else
        read -p "$prompt: " value
    fi
    
    echo "$value"
}

# Function to prompt for password
prompt_password() {
    local prompt="$1"
    local password
    
    while true; do
        read -s -p "$prompt: " password
        echo
        if [ -n "$password" ]; then
            read -s -p "Confirm password: " password_confirm
            echo
            if [ "$password" = "$password_confirm" ]; then
                break
            else
                echo -e "${RED}❌ Passwords don't match. Please try again.${NC}"
            fi
        else
            echo -e "${RED}❌ Password cannot be empty. Please try again.${NC}"
        fi
    done
    
    echo "$password"
}

echo -e "${BLUE}📋 MariaDB Server Configuration${NC}"
echo

# Check if MariaDB server is installed
if ! command -v mariadb &> /dev/null && ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}📦 MariaDB server not found. Installing...${NC}"
    
    # Detect OS and install MariaDB
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y mariadb-server mariadb-client
        elif command -v yum &> /dev/null; then
            sudo yum install -y mariadb-server mariadb
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y mariadb-server mariadb
        else
            echo -e "${RED}❌ Unsupported Linux distribution${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install mariadb
        else
            echo -e "${RED}❌ Homebrew not found. Please install MariaDB manually${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported operating system${NC}"
        exit 1
    fi
fi

# Start MariaDB service if not running
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! systemctl is-active --quiet mariadb; then
        echo -e "${YELLOW}🔄 Starting MariaDB service...${NC}"
        sudo systemctl start mariadb
        sudo systemctl enable mariadb
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew services list | grep mariadb | grep started &> /dev/null; then
        echo -e "${YELLOW}🔄 Starting MariaDB service...${NC}"
        brew services start mariadb
    fi
fi

echo -e "${GREEN}✅ MariaDB server is running${NC}"
echo

# Get database configuration
echo -e "${BLUE}🔧 Database Configuration${NC}"
DB_NAME=$(prompt_input "Database name" "exo_cluster")
DB_USER=$(prompt_input "Database user" "exo_ai")
DB_HOST=$(prompt_input "Database host" "localhost")
DB_PORT=$(prompt_input "Database port" "3306")

echo
echo -e "${BLUE}🔐 Password Setup${NC}"
ROOT_PASSWORD=$(prompt_password "MariaDB root password (leave empty if not set)")
USER_PASSWORD=$(prompt_password "Password for $DB_USER")

echo
echo -e "${BLUE}📊 Creating database and user...${NC}"

# Create database and user
MYSQL_CMD="mariadb"
if ! command -v mariadb &> /dev/null; then
    MYSQL_CMD="mysql"
fi

# Build connection command
CONNECT_CMD="$MYSQL_CMD -h $DB_HOST -P $DB_PORT -u root"
if [ -n "$ROOT_PASSWORD" ]; then
    CONNECT_CMD="$CONNECT_CMD -p$ROOT_PASSWORD"
fi

# Create database and user
SQL_COMMANDS="
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$USER_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE, SHOW VIEW ON $DB_NAME.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
"

echo "$SQL_COMMANDS" | $CONNECT_CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database and user created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create database and user${NC}"
    echo "Please check your root password and try again"
    exit 1
fi

# Create configuration file
echo
echo -e "${BLUE}📝 Creating configuration file...${NC}"

CONFIG_FILE="db_config.json"
cat > "$CONFIG_FILE" << EOF
{
  "host": "$DB_HOST",
  "port": $DB_PORT,
  "user": "$DB_USER",
  "password": "$USER_PASSWORD",
  "database": "$DB_NAME",
  "charset": "utf8mb4",
  "max_connections": 20,
  "connection_timeout": 30,
  "read_timeout": 60,
  "write_timeout": 60
}
EOF

echo -e "${GREEN}✅ Configuration saved to $CONFIG_FILE${NC}"

# Set secure permissions
chmod 600 "$CONFIG_FILE"
echo -e "${GREEN}✅ Configuration file permissions set to 600${NC}"

# Create sample tables for demonstration
echo
echo -e "${BLUE}📊 Creating sample tables...${NC}"

SAMPLE_SQL="
USE $DB_NAME;

-- AI Models table
CREATE TABLE IF NOT EXISTS ai_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    parameters BIGINT,
    memory_usage_gb DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_type (model_type)
);

-- Cluster Nodes table
CREATE TABLE IF NOT EXISTS cluster_nodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_id VARCHAR(100) UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    cpu_cores INT,
    memory_gb INT,
    gpu_memory_gb INT DEFAULT 0,
    status ENUM('online', 'offline', 'maintenance') DEFAULT 'offline',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_node_id (node_id),
    INDEX idx_status (status)
);

-- Query Log table for auditing
CREATE TABLE IF NOT EXISTS query_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query_hash VARCHAR(32) NOT NULL,
    query_text TEXT,
    user_context VARCHAR(100),
    execution_time DECIMAL(10,6),
    rows_affected INT,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hash (query_hash),
    INDEX idx_context (user_context),
    INDEX idx_created (created_at)
);

-- Insert sample data
INSERT IGNORE INTO ai_models (name, model_type, parameters, memory_usage_gb) VALUES
('Llama-3.1-8B', 'language', 8000000000, 16.0),
('Llama-3.1-70B', 'language', 70000000000, 140.0),
('Claude-3.5-Sonnet', 'language', 175000000000, 350.0),
('GPT-4', 'language', 1760000000000, 3520.0);

-- Insert cluster information (example for Mac M4 Studios)
INSERT IGNORE INTO cluster_nodes (node_id, hostname, ip_address, cpu_cores, memory_gb, gpu_memory_gb, status) VALUES
('mac-studio-1', 'mac-studio-01.local', '192.168.1.101', 12, 128, 128, 'online'),
('mac-studio-2', 'mac-studio-02.local', '192.168.1.102', 12, 128, 128, 'online'),
('mac-studio-3', 'mac-studio-03.local', '192.168.1.103', 12, 128, 128, 'online');
"

echo "$SAMPLE_SQL" | $CONNECT_CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Sample tables created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Some sample tables may not have been created${NC}"
fi

# Test the connection
echo
echo -e "${BLUE}🧪 Testing database connection...${NC}"

# Make db_shell.py executable
chmod +x db_shell.py

# Test with our database shell
if python3 db_shell.py --config "$CONFIG_FILE" --test; then
    echo -e "${GREEN}✅ Database connection test successful!${NC}"
else
    echo -e "${RED}❌ Database connection test failed${NC}"
    echo "Please check your configuration and try again"
fi

echo
echo -e "${GREEN}🎉 MariaDB setup completed successfully!${NC}"
echo
echo -e "${BLUE}📋 Summary:${NC}"
echo "• Database: $DB_NAME"
echo "• User: $DB_USER"
echo "• Host: $DB_HOST:$DB_PORT"
echo "• Config file: $CONFIG_FILE"
echo
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "1. Test the database shell:"
echo "   python3 db_shell.py --config $CONFIG_FILE"
echo
echo "2. Start your exo cluster with database tools enabled"
echo "3. Models can now use database functions:"
echo "   - query_database()"
echo "   - get_database_schema()"
echo "   - test_database_connection()"
echo
echo -e "${YELLOW}🔒 Security Notes:${NC}"
echo "• Configuration file contains passwords - keep it secure!"
echo "• User '$DB_USER' has limited privileges (no DDL operations)"
echo "• All queries are validated for security before execution"
echo "• Query history is logged for auditing"
echo
echo -e "${BLUE}💡 Environment Variables (alternative to config file):${NC}"
echo "export MARIADB_HOST='$DB_HOST'"
echo "export MARIADB_PORT='$DB_PORT'"
echo "export MARIADB_USER='$DB_USER'"
echo "export MARIADB_PASSWORD='$USER_PASSWORD'"
echo "export MARIADB_DATABASE='$DB_NAME'"