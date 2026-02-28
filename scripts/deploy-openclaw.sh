#!/bin/bash
set -e

# AiFood OpenClaw Plugin Deploy Script
# Server: 199.247.30.52

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLUGIN_DIR="$PROJECT_DIR/aifood-plugin"

echo "=== AiFood OpenClaw Plugin Deploy ==="
echo "Project: $PROJECT_DIR"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed!"
    exit 1
fi

echo "Docker version: $(docker --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Start PostgreSQL via Docker
echo "Starting PostgreSQL container..."
cd "$PROJECT_DIR"

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q '^aifood-postgres$'; then
    # Container exists, start it if not running
    if ! docker ps --format '{{.Names}}' | grep -q '^aifood-postgres$'; then
        docker start aifood-postgres
    fi
    echo "PostgreSQL container already running"
else
    # Create new container
    docker compose up -d postgres
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
sleep 5
docker exec aifood-postgres pg_isready -U aifood -d aifood || {
    echo "Waiting more for PostgreSQL..."
    sleep 10
}

# Pull latest code
echo "Pulling latest code..."
git fetch origin main
git reset --hard origin/main

# Install dependencies
echo "Installing npm dependencies..."
cd "$PLUGIN_DIR"
npm install

# Build plugin
echo "Building TypeScript..."
npm run build

# Check OpenClaw installation
if ! command -v openclaw &> /dev/null; then
    echo ""
    echo "WARNING: OpenClaw CLI not found!"
    echo "Install OpenClaw first: https://openclaw.ai/docs/installation"
    echo ""
    echo "After installing OpenClaw, run:"
    echo "  openclaw plugins install $PLUGIN_DIR"
    echo ""
else
    # Install plugin to OpenClaw
    echo "Installing plugin to OpenClaw..."
    openclaw plugins install "$PLUGIN_DIR"

    echo ""
    echo "Plugin installed! Configure it in ~/.openclaw/openclaw.json"
fi

echo ""
echo "=== Deploy complete ==="
echo ""
echo "PostgreSQL running in Docker on port 5433"
echo ""
echo "Next steps:"
echo "1. Configure OpenClaw plugin in ~/.openclaw/openclaw.json:"
echo '   {
     "plugins": {
       "entries": {
         "aifood": {
           "config": {
             "fatsecretClientId": "YOUR_CLIENT_ID",
             "fatsecretClientSecret": "YOUR_SECRET",
             "databaseUrl": "postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood"
           }
         }
       }
     }
   }'
echo ""
echo "2. Restart OpenClaw gateway"
