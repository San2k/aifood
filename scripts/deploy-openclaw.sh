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

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Create database if not exists
echo "Setting up database..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'aifood'" | grep -q 1 || \
    sudo -u postgres createdb aifood

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = 'aifood'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER aifood WITH PASSWORD 'aifood_secure_password_2024';"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE aifood TO aifood;"

# Pull latest code
echo "Pulling latest code..."
cd "$PROJECT_DIR"
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
echo "Next steps:"
echo "1. Configure OpenClaw plugin in ~/.openclaw/openclaw.json:"
echo '   {
     "plugins": {
       "entries": {
         "aifood": {
           "config": {
             "fatsecretClientId": "YOUR_CLIENT_ID",
             "fatsecretClientSecret": "YOUR_SECRET",
             "databaseUrl": "postgresql://aifood:aifood_secure_password_2024@localhost:5432/aifood"
           }
         }
       }
     }
   }'
echo ""
echo "2. Restart OpenClaw gateway"
