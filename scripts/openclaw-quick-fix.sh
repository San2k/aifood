#!/bin/bash
# OpenClaw Quick Fix Script
# Usage: ./scripts/openclaw-quick-fix.sh <API_KEY>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <GEMINI_API_KEY>"
    echo "Example: $0 AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs"
    exit 1
fi

API_KEY="$1"
SERVER="gpu-server"

echo "🔧 Updating OpenClaw configuration with new API key..."
echo ""

# Update root auth-profiles.json
echo "📝 Updating root auth-profiles.json..."
ssh $SERVER "cat > ~/.openclaw/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"$API_KEY\"
    }
  }
}
EOF"

# Update agent auth-profiles.json (CRITICAL!)
echo "📝 Updating agent auth-profiles.json (CRITICAL!)..."
ssh $SERVER "cat > ~/.openclaw/agents/main/agent/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"$API_KEY\"
    }
  },
  \"usageStats\": {
    \"google:default\": {
      \"errorCount\": 0,
      \"lastUsed\": $(date +%s)000
    }
  }
}
EOF"

# Update systemd service
echo "📝 Updating systemd service environment..."
ssh $SERVER "cat > /etc/systemd/system/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=\"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
Environment=\"NODE_ENV=production\"
Environment=\"OPENAI_API_KEY=sk-vKMa0DfKO4yZs8GvsxT89Bt9vJeMY7NRPL8VxZvSmLDMjLs4\"
Environment=\"OPENAI_BASE_URL=https://api.moonshot.ai/v1\"
Environment=\"OPENAI_MODEL=moonshot-v1-128k\"
Environment=\"GOOGLE_API_KEY=$API_KEY\"
Environment=\"GEMINI_API_KEY=$API_KEY\"
ExecStart=/usr/bin/openclaw gateway run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=openclaw-gateway

[Install]
WantedBy=multi-user.target
EOF"

# Reload and restart
echo "🔄 Reloading systemd and restarting OpenClaw Gateway..."
ssh $SERVER "systemctl daemon-reload"
ssh $SERVER "systemctl restart openclaw-gateway"

echo ""
echo "⏳ Waiting for service to start..."
sleep 5

# Check status
echo ""
echo "✅ Checking service status..."
ssh $SERVER "systemctl status openclaw-gateway --no-pager | head -15"

echo ""
echo "📋 Recent logs (checking for errors)..."
ssh $SERVER "journalctl -u openclaw-gateway --since '1 minute ago' --no-pager | grep -i error || echo 'No errors found ✅'"

echo ""
echo "✅ OpenClaw configuration updated successfully!"
echo ""
echo "📝 Files updated:"
echo "  - /root/.openclaw/auth-profiles.json"
echo "  - /root/.openclaw/agents/main/agent/auth-profiles.json"
echo "  - /etc/systemd/system/openclaw-gateway.service"
echo ""
echo "🔍 Test in Telegram: Send a message to @LenoxAI_bot"
echo ""
