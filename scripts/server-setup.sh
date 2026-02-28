#!/bin/bash
set -e

# Initial Server Setup for AiFood OpenClaw Plugin
# Run this ONCE on a fresh server

echo "=== AiFood Server Initial Setup ==="
echo "Server: $(hostname)"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essentials
echo "Installing essential packages..."
sudo apt-get install -y \
    curl \
    git \
    build-essential \
    ca-certificates \
    gnupg

# Install Node.js 20
echo "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

# Install PostgreSQL
echo "Installing PostgreSQL..."
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
echo "Setting up PostgreSQL database..."
sudo -u postgres psql <<EOF
CREATE USER aifood WITH PASSWORD 'aifood_secure_password_2024';
CREATE DATABASE aifood OWNER aifood;
GRANT ALL PRIVILEGES ON DATABASE aifood TO aifood;
EOF

# Clone repository
echo "Cloning repository..."
sudo mkdir -p /opt/aifood
sudo chown $USER:$USER /opt/aifood
cd /opt
git clone https://github.com/San2k/aifood.git aifood

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
echo "postgresql://aifood:aifood_secure_password_2024@localhost:5432/aifood"
