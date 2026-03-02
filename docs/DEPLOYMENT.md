# AiFood Deployment Guide

Production deployment guide for AiFood OpenClaw plugin on Ubuntu server.

## Server Specifications

**Current Production Server:**
- IP: `199.247.30.52`
- OS: Ubuntu 24.04 LTS
- CPU: CPU-only (no GPU)
- RAM: 16GB
- Storage: NVMe SSD
- Services: OpenClaw Gateway, PostgreSQL, Ollama (optional)

## Prerequisites

### System Requirements

**Minimum:**
- Ubuntu 22.04+ or Debian 11+
- 2 CPU cores
- 4GB RAM
- 20GB storage

**Recommended:**
- Ubuntu 24.04 LTS
- 4+ CPU cores
- 8GB+ RAM
- 50GB NVMe SSD

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18+ (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16

# Install build tools
sudo apt install -y build-essential git curl
```

## Installation Steps

### 1. PostgreSQL Setup

```bash
# Switch to postgres user
sudo -i -u postgres

# Create database and user
createuser aifood
createdb aifood -O aifood

# Set password
psql -c "ALTER USER aifood WITH PASSWORD 'YOUR_SECURE_PASSWORD';"

# Configure PostgreSQL to listen on custom port
sudo nano /etc/postgresql/16/main/postgresql.conf
# Change: port = 5433

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Clone Repository

```bash
# Clone to /opt/aifood
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/AiFood.git aifood
sudo chown -R $USER:$USER /opt/aifood
cd /opt/aifood
```

### 3. Build Plugin

```bash
cd /opt/aifood/aifood-plugin

# Install dependencies (production only)
npm install --production

# Build TypeScript
npm run build

# Verify build
ls -la dist/
# Should see: index.js, index.d.ts, index.js.map, etc.
```

### 4. Install OpenClaw

```bash
# Install OpenClaw CLI
curl -fsSL https://openclaw.com/install.sh | sh

# Verify installation
openclaw --version

# Run initial configuration
openclaw configure

# This creates ~/.openclaw/openclaw.json
```

### 5. Configure OpenClaw

Edit `~/.openclaw/openclaw.json`:

```json
{
  "meta": {
    "lastTouchedVersion": "2026.2.25"
  },
  "update": {
    "channel": "stable"
  },
  "auth": {
    "profiles": {
      "google:default": {
        "provider": "google",
        "mode": "api_key"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.0-flash-exp",
        "fallbacks": []
      },
      "workspace": "~/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN_FROM_BOTFATHER",
      "dmPolicy": "open",
      "groupPolicy": "allowlist",
      "streaming": "partial",
      "allowFrom": ["*"]
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token"
    }
  },
  "plugins": {
    "entries": {
      "telegram": {
        "enabled": true
      },
      "aifood": {
        "enabled": true
      }
    },
    "installs": {
      "aifood": {
        "source": "path",
        "sourcePath": "/opt/aifood/aifood-plugin",
        "installPath": "~/.openclaw/extensions/aifood",
        "version": "1.0.0"
      }
    }
  }
}
```

### 6. Configure Google AI API Key

Edit `~/.openclaw/agents/main/agent/auth.json`:

```json
{
  "google": {
    "type": "api_key",
    "key": "YOUR_GOOGLE_AI_API_KEY"
  }
}
```

Get API key: https://aistudio.google.com/apikey

### 7. Configure Plugin Settings

Plugin config is in main `openclaw.json` under `plugins.entries.aifood.config`:

Add this section:

```json
{
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "fatsecretClientId": "YOUR_FATSECRET_CLIENT_ID",
          "fatsecretClientSecret": "YOUR_FATSECRET_CLIENT_SECRET",
          "databaseUrl": "postgresql://aifood:YOUR_PASSWORD@localhost:5433/aifood"
        }
      }
    }
  }
}
```

Get FatSecret credentials: https://platform.fatsecret.com/api/

### 8. Install Plugin

```bash
# Install plugin to OpenClaw
openclaw plugins install /opt/aifood/aifood-plugin

# Verify installation
openclaw plugins list
# Should show: aifood@1.0.0
```

### 9. Setup Systemd Service

Create `/etc/systemd/system/openclaw-gateway.service`:

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/openclaw gateway run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable openclaw-gateway

# Start service
sudo systemctl start openclaw-gateway

# Check status
sudo systemctl status openclaw-gateway

# View logs
journalctl -u openclaw-gateway -f
```

## Verification

### 1. Check Services

```bash
# OpenClaw Gateway
sudo systemctl status openclaw-gateway

# PostgreSQL
sudo systemctl status postgresql

# Check OpenClaw logs
journalctl -u openclaw-gateway --since "5 minutes ago" --no-pager
```

### 2. Test Database Connection

```bash
# Connect to database
psql -h localhost -p 5433 -U aifood -d aifood

# List tables
\dt

# Check user_profile table
SELECT * FROM user_profile LIMIT 5;

# Exit
\q
```

### 3. Test Plugin

```bash
# Check plugin loaded
journalctl -u openclaw-gateway | grep -i "aifood"

# Should see:
# [gateway] AiFood: Plugin registered with X tools
```

### 4. Test Telegram Bot

1. Open Telegram
2. Find your bot (@YourBotName)
3. Send: `/start`
4. Send: "Съел 2 яйца"
5. Verify bot responds

## Updating

### Update Plugin Code

```bash
cd /opt/aifood

# Pull latest changes
git pull origin main

# Rebuild plugin
cd aifood-plugin
npm install --production
npm run build

# Restart OpenClaw
sudo systemctl restart openclaw-gateway

# Verify
journalctl -u openclaw-gateway -f
```

### Update OpenClaw

```bash
# Update OpenClaw CLI
openclaw update

# Restart service
sudo systemctl restart openclaw-gateway
```

## Monitoring

### View Logs

```bash
# Real-time logs
journalctl -u openclaw-gateway -f

# Last 100 lines
journalctl -u openclaw-gateway -n 100 --no-pager

# Errors only
journalctl -u openclaw-gateway -p err --since today

# Specific time range
journalctl -u openclaw-gateway --since "2 hours ago" --until "1 hour ago"
```

### Check Resource Usage

```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
top

# Service memory
systemctl status openclaw-gateway | grep Memory
```

### Database Monitoring

```bash
# Active connections
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT pg_size_pretty(pg_database_size('aifood'));"

# Table sizes
psql -h localhost -p 5433 -U aifood -d aifood -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Troubleshooting

### Plugin Not Loading

```bash
# Check plugin path
openclaw plugins list

# Verify build
ls -la /opt/aifood/aifood-plugin/dist/

# Check OpenClaw logs for errors
journalctl -u openclaw-gateway | grep -i "error\|warning"

# Reinstall plugin
openclaw plugins uninstall aifood
openclaw plugins install /opt/aifood/aifood-plugin
sudo systemctl restart openclaw-gateway
```

### Database Connection Failed

```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Check port
sudo netstat -tlnp | grep 5433

# Test connection
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT 1;"

# Check credentials in openclaw.json
cat ~/.openclaw/openclaw.json | grep databaseUrl
```

### Bot Not Responding

```bash
# Check gateway running
sudo systemctl status openclaw-gateway

# Check Telegram connection
journalctl -u openclaw-gateway | grep -i telegram

# Verify bot token
cat ~/.openclaw/openclaw.json | grep botToken

# Check for errors
journalctl -u openclaw-gateway -p err --since "10 minutes ago"
```

### High Memory Usage

```bash
# Check memory
free -h

# Identify process
ps aux --sort=-%mem | head -10

# Restart gateway
sudo systemctl restart openclaw-gateway

# Check after restart
systemctl status openclaw-gateway
```

## Backup

### Database Backup

```bash
# Create backup directory
mkdir -p /opt/aifood/backups

# Backup database
pg_dump -h localhost -p 5433 -U aifood -d aifood > /opt/aifood/backups/aifood_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip /opt/aifood/backups/aifood_*.sql

# List backups
ls -lh /opt/aifood/backups/
```

### Restore from Backup

```bash
# Stop services
sudo systemctl stop openclaw-gateway

# Drop and recreate database
sudo -u postgres dropdb aifood
sudo -u postgres createdb aifood -O aifood

# Restore
gunzip < /opt/aifood/backups/aifood_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -p 5433 -U aifood -d aifood

# Restart services
sudo systemctl start openclaw-gateway
```

### Automated Backups

Create `/etc/cron.daily/aifood-backup`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/aifood/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h localhost -p 5433 -U aifood -d aifood | gzip > ${BACKUP_DIR}/aifood_${DATE}.sql.gz

# Keep only last 7 days
find ${BACKUP_DIR} -name "aifood_*.sql.gz" -mtime +7 -delete

echo "Backup completed: aifood_${DATE}.sql.gz"
```

Make executable:

```bash
sudo chmod +x /etc/cron.daily/aifood-backup
```

## Security

### Firewall Configuration

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow PostgreSQL (if remote access needed)
# sudo ufw allow from YOUR_IP to any port 5433

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### SSL/TLS (Optional)

For production with external database access:

```bash
# Generate self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/postgres.key \
  -out /etc/ssl/certs/postgres.crt

# Configure PostgreSQL SSL
sudo nano /etc/postgresql/16/main/postgresql.conf
# Add:
# ssl = on
# ssl_cert_file = '/etc/ssl/certs/postgres.crt'
# ssl_key_file = '/etc/ssl/private/postgres.key'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update OpenClaw
openclaw update

# Update plugin
cd /opt/aifood && git pull origin main
cd aifood-plugin && npm install --production && npm run build
sudo systemctl restart openclaw-gateway
```

## Performance Tuning

### PostgreSQL Optimization

Edit `/etc/postgresql/16/main/postgresql.conf`:

```ini
# For 16GB RAM server
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### OpenClaw Memory Limits

Edit systemd service to limit memory:

```ini
[Service]
MemoryLimit=2G
```

Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart openclaw-gateway
```

## Support

For issues:
- GitHub Issues: https://github.com/YOUR_USERNAME/AiFood/issues
- OpenClaw Docs: https://docs.openclaw.ai
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

Last Updated: March 2026
