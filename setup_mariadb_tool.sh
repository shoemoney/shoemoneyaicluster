#!/bin/bash

# MariaDB Tool Setup Script for Mac M4 Studio Cluster
echo "=== MariaDB Tool Setup for AI Model Cluster ==="
echo "Total cluster memory: 2.4TB across Mac M4 Studios"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install aiomysql pymysql cryptography

# Create config directory
mkdir -p config

# Create configuration template
cat > config/mariadb_config.json << CONFIGEOF
{
  "host": "${MARIADB_HOST:-localhost}",
  "port": ${MARIADB_PORT:-3306},
  "user": "${MARIADB_USER:-root}",
  "password": "${MARIADB_PASSWORD:-}",
  "database": "${MARIADB_DATABASE:-ai_models}",
  "pool_size": 20,
  "charset": "utf8mb4"
}
CONFIGEOF

echo "Configuration created at config/mariadb_config.json"
echo "Please update it with your MariaDB credentials"

# Create environment file
cat > .env.mariadb << ENVEOF
export MARIADB_HOST="${MARIADB_HOST:-localhost}"
export MARIADB_PORT="${MARIADB_PORT:-3306}"
export MARIADB_USER="${MARIADB_USER:-root}"
export MARIADB_PASSWORD="${MARIADB_PASSWORD:-}"
export MARIADB_DATABASE="${MARIADB_DATABASE:-ai_models}"
export MARIADB_CONFIG_FILE="config/mariadb_config.json"
ENVEOF

echo "Environment file created at .env.mariadb"
echo "Source it with: source .env.mariadb"
