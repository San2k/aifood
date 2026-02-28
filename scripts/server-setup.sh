#!/bin/bash
set -e

# Initial Server Setup for AiFood OpenClaw Plugin
# Run this ONCE on a fresh server

echo "=== AiFood Server Initial Setup ==="
echo "Server: $(hostname)"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is required but not installed!"
    echo "Install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "Docker: $(docker --version)"

# Install Node.js if needed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

# Clone repository
echo "Cloning repository..."
sudo mkdir -p /opt/aifood
sudo chown $USER:$USER /opt/aifood
cd /opt
if [ -d "/opt/aifood/.git" ]; then
    echo "Repository already exists, pulling latest..."
    cd /opt/aifood
    git fetch origin main
    git reset --hard origin/main
else
    git clone https://github.com/San2k/aifood.git aifood
    cd /opt/aifood
fi

# Start PostgreSQL via Docker
echo "Starting PostgreSQL container..."
docker compose up -d postgres

# Wait for PostgreSQL
echo "Waiting for PostgreSQL to be ready..."
sleep 5
docker exec aifood-postgres pg_isready -U aifood -d aifood || sleep 10

# Build plugin
echo "Building plugin..."
cd /opt/aifood/aifood-plugin
npm install
npm run build

echo ""
echo "=== Initial setup complete ==="
echo ""
echo "Next:"
echo "1. Install OpenClaw: https://openclaw.ai/docs/installation"
echo "2. Run: openclaw plugins install /opt/aifood/aifood-plugin"
echo "3. Configure ~/.openclaw/openclaw.json with FatSecret credentials"
echo ""
echo "Database connection string:"
echo "postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood"
