# OpenClaw Configuration Guide

**Last Updated**: 2026-03-04 06:30 UTC
**Server**: 199.247.7.186 (gpu-server)

## Configuration Files Location

| File | Location | Purpose |
|------|----------|---------|
| **Main Config** | `/root/.openclaw/openclaw.json` | OpenClaw gateway configuration |
| **Root Auth** | `/root/.openclaw/auth-profiles.json` | API keys for providers (root level) |
| **Agent Auth** | `/root/.openclaw/agents/main/agent/auth-profiles.json` | API keys for agent (critical!) |
| **Systemd Service** | `/etc/systemd/system/openclaw-gateway.service` | Environment variables & startup |
| **LLM Gateway Env** | `/opt/aifood/.env` | LLM Gateway API keys |

---

## 1. Main Configuration (`openclaw.json`)

**Location**: `/root/.openclaw/openclaw.json`

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.5-flash",
        "fallbacks": []
      },
      "compaction": {
        "mode": "safeguard"
      }
    }
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true,
    "ownerDisplay": "raw"
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "open",
      "botToken": "8205605578:AAHx_Be6RJL6Q7sQxhSTTXjYdl6eRkXJPF8",
      "allowFrom": ["*"],
      "groupPolicy": "allowlist",
      "streaming": "partial"
    }
  },
  "gateway": {
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "0927fe382cf1b27fb5a95646b2178b21e9529d93a9437c11"
    }
  },
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "databaseUrl": "postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood"
        }
      }
    }
  },
  "meta": {
    "lastTouchedVersion": "2026.3.2",
    "lastTouchedAt": "2026-03-04T06:30:00.000Z"
  }
}
```

### Key Settings:
- **Model**: `google/gemini-2.5-flash` (IMPORTANT: must be valid model from Google)
- **Telegram Bot**: Token for @LenoxAI_bot
- **AiFood Plugin**: PostgreSQL connection string

### How to Update:
```bash
ssh gpu-server "nano ~/.openclaw/openclaw.json"
# OR
ssh gpu-server "cat > ~/.openclaw/openclaw.json << 'EOF'
{...}
EOF"
```

---

## 2. Authentication Profiles (CRITICAL!)

### 2.1 Root Level Auth

**Location**: `/root/.openclaw/auth-profiles.json`

```json
{
  "version": 1,
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs"
    }
  }
}
```

### 2.2 Agent Level Auth (MOST IMPORTANT!)

**Location**: `/root/.openclaw/agents/main/agent/auth-profiles.json`

```json
{
  "version": 1,
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs"
    }
  },
  "usageStats": {
    "google:default": {
      "errorCount": 0,
      "lastUsed": 1772605588328
    }
  }
}
```

### ⚠️ CRITICAL: Update Both Files!

When changing API key, you MUST update BOTH files:

```bash
# Update root auth
ssh gpu-server "cat > ~/.openclaw/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"YOUR_NEW_KEY\"
    }
  }
}
EOF"

# Update agent auth (CRITICAL!)
ssh gpu-server "cat > ~/.openclaw/agents/main/agent/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"YOUR_NEW_KEY\"
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

# Restart OpenClaw
ssh gpu-server "systemctl restart openclaw-gateway"
```

---

## 3. Systemd Service Configuration

**Location**: `/etc/systemd/system/openclaw-gateway.service`

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="NODE_ENV=production"
Environment="OPENAI_API_KEY=sk-vKMa0DfKO4yZs8GvsxT89Bt9vJeMY7NRPL8VxZvSmLDMjLs4"
Environment="OPENAI_BASE_URL=https://api.moonshot.ai/v1"
Environment="OPENAI_MODEL=moonshot-v1-128k"
Environment="GOOGLE_API_KEY=AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs"
Environment="GEMINI_API_KEY=AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs"
ExecStart=/usr/bin/openclaw gateway run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=openclaw-gateway

[Install]
WantedBy=multi-user.target
```

### Environment Variables:
- **GOOGLE_API_KEY**: Gemini API key (required for google/* models)
- **GEMINI_API_KEY**: Alternative name for Gemini key
- **OPENAI_API_KEY**: Moonshot AI key (for fallback)

### How to Update:
```bash
ssh gpu-server "cat > /etc/systemd/system/openclaw-gateway.service << 'EOF'
[Service section with new Environment variables]
EOF"

ssh gpu-server "systemctl daemon-reload"
ssh gpu-server "systemctl restart openclaw-gateway"
```

---

## 4. LLM Gateway Configuration

**Location**: `/opt/aifood/.env`

```env
# Gemini API
GEMINI_API_KEY=AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs
GEMINI_MODEL=gemini-2.5-flash

# PostgreSQL
POSTGRES_PASSWORD=aifood_secure_password_2024

# Token Policy
HISTORY_WINDOW_TOKENS=12000
HISTORY_WINDOW_MESSAGES=8
SUMMARY_TRIGGER_TOKENS=12000
SUMMARY_TARGET_TOKENS=1000

# Cache
CACHE_ENABLED=true
CACHE_TTL=3600
REDIS_URL=redis://redis:6379/1

# Quotas
QUOTA_DAILY_TOKENS=100000
QUOTA_MONTHLY_USD=50
```

### How to Update:
```bash
ssh gpu-server "cd /opt/aifood && nano .env"

# Restart LLM Gateway
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"
```

---

## Troubleshooting: API Key Issues

### Problem: "API key expired" error

**Root Cause**: Old/wrong API key in agent auth file

**Solution**:
```bash
# 1. Check which key is being used
ssh gpu-server "cat ~/.openclaw/agents/main/agent/auth-profiles.json | grep key"

# 2. Verify current API key works
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | head -20'

# 3. Update BOTH auth files (see section 2.2 above)

# 4. Restart OpenClaw
ssh gpu-server "systemctl restart openclaw-gateway"

# 5. Verify no errors
ssh gpu-server "journalctl -u openclaw-gateway --since '1 minute ago' --no-pager | grep -i error"
```

### Problem: Model not found (404)

**Available Models**:
- ✅ `gemini-2.5-flash` (recommended)
- ✅ `gemini-2.5-pro`
- ✅ `gemini-2.0-flash`
- ❌ `gemini-1.5-flash` (DOES NOT EXIST)

**Fix**:
```bash
# Update openclaw.json with correct model
ssh gpu-server "nano ~/.openclaw/openclaw.json"
# Change: "primary": "google/gemini-2.5-flash"

ssh gpu-server "systemctl restart openclaw-gateway"
```

---

## Configuration Backup

### Create Backup:
```bash
ssh gpu-server "tar -czf ~/openclaw-config-backup-$(date +%Y%m%d).tar.gz \
  ~/.openclaw/openclaw.json \
  ~/.openclaw/auth-profiles.json \
  ~/.openclaw/agents/main/agent/auth-profiles.json \
  /etc/systemd/system/openclaw-gateway.service"
```

### Restore Backup:
```bash
ssh gpu-server "tar -xzf ~/openclaw-config-backup-YYYYMMDD.tar.gz -C /"
ssh gpu-server "systemctl daemon-reload && systemctl restart openclaw-gateway"
```

---

## Quick Reference Commands

```bash
# View main config
ssh gpu-server "cat ~/.openclaw/openclaw.json"

# View auth profiles
ssh gpu-server "cat ~/.openclaw/auth-profiles.json"
ssh gpu-server "cat ~/.openclaw/agents/main/agent/auth-profiles.json"

# View systemd service
ssh gpu-server "systemctl cat openclaw-gateway"

# Check environment variables in running process
ssh gpu-server "cat /proc/\$(systemctl show -p MainPID openclaw-gateway | cut -d= -f2)/environ | tr '\\0' '\\n' | grep -E '(GOOGLE|GEMINI)'"

# Restart OpenClaw
ssh gpu-server "systemctl restart openclaw-gateway"

# Check logs
ssh gpu-server "journalctl -u openclaw-gateway -f"

# Test API key
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | head -20'
```

---

## Important Notes

1. **Agent Auth is Critical**: The file `~/.openclaw/agents/main/agent/auth-profiles.json` is the PRIMARY auth file used by OpenClaw. Always update it when changing keys.

2. **Both Files Required**: Update BOTH auth files (root + agent) to avoid confusion.

3. **Systemd Variables**: Environment variables in systemd service are fallback - auth-profiles.json takes precedence.

4. **Model Names**: Always use valid model names from Google API. Check with:
   ```bash
   curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | jq '.models[].name'
   ```

5. **Restart After Changes**: Always restart OpenClaw after config changes:
   ```bash
   systemctl restart openclaw-gateway
   ```

---

## Current API Key (2026-03-04)

**Active Key**: `AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs`
**Status**: ✅ Working
**Updated**: 2026-03-04 06:30 UTC
**Location**: Both auth-profiles.json files + systemd service

**Previous Key** (LEAKED, DISABLED): `AIzaSyAq1AoNdzjLXmxXl3uVq8UZu_shTDmlTVY`
