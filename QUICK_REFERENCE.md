# AiFood - Quick Reference

⚡ **Quick links for common tasks**

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [OPENCLAW_CONFIG.md](OPENCLAW_CONFIG.md) | Complete OpenClaw configuration guide |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Production deployment status & monitoring |
| [scripts/README.md](scripts/README.md) | Available scripts and usage |

---

## 🔑 Critical Configuration Files

**⚠️ MOST IMPORTANT**: `/root/.openclaw/agents/main/agent/auth-profiles.json`

| File | Location |
|------|----------|
| Main Config | `/root/.openclaw/openclaw.json` |
| Root Auth | `/root/.openclaw/auth-profiles.json` |
| **Agent Auth** | `/root/.openclaw/agents/main/agent/auth-profiles.json` |
| Systemd Service | `/etc/systemd/system/openclaw-gateway.service` |
| LLM Gateway Env | `/opt/aifood/.env` |

---

## 🚀 Quick Commands

### Server Access
```bash
ssh gpu-server  # 199.247.7.186
```

### OpenClaw Gateway
```bash
# Status
ssh gpu-server "systemctl status openclaw-gateway"

# Restart
ssh gpu-server "systemctl restart openclaw-gateway"

# Logs (live)
ssh gpu-server "journalctl -u openclaw-gateway -f"

# Logs (recent errors)
ssh gpu-server "journalctl -u openclaw-gateway --since '5 minutes ago' | grep -i error"
```

### LLM Gateway
```bash
# Status
ssh gpu-server "cd /opt/aifood && docker compose ps llm-gateway"

# Health check
ssh gpu-server "curl -s http://localhost:9000/health"

# Logs
ssh gpu-server "cd /opt/aifood && docker compose logs -f llm-gateway"

# Restart
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"
```

### Check API Key
```bash
# View current key in agent config
ssh gpu-server "cat ~/.openclaw/agents/main/agent/auth-profiles.json | grep key"

# Test key works
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | head -20'
```

---

## 🔧 Fix Common Issues

### "API Key Expired" Error

**Quick Fix Script**:
```bash
./scripts/openclaw-quick-fix.sh AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs
```

**Manual Fix**:
```bash
# Update BOTH auth files (root + agent)
ssh gpu-server "cat > ~/.openclaw/auth-profiles.json << 'EOF'
{\"version\":1,\"profiles\":{\"google:default\":{\"type\":\"api_key\",\"provider\":\"google\",\"key\":\"NEW_KEY\"}}}
EOF"

ssh gpu-server "cat > ~/.openclaw/agents/main/agent/auth-profiles.json << 'EOF'
{\"version\":1,\"profiles\":{\"google:default\":{\"type\":\"api_key\",\"provider\":\"google\",\"key\":\"NEW_KEY\"}}}
EOF"

# Restart
ssh gpu-server "systemctl restart openclaw-gateway"
```

### Model Not Found (404)

**Valid Models**:
- ✅ `gemini-2.5-flash` (recommended)
- ✅ `gemini-2.5-pro`
- ✅ `gemini-2.0-flash`
- ❌ `gemini-1.5-flash` (DOES NOT EXIST)

**Fix**:
```bash
ssh gpu-server "nano ~/.openclaw/openclaw.json"
# Change: "primary": "google/gemini-2.5-flash"
ssh gpu-server "systemctl restart openclaw-gateway"
```

### LLM Gateway Not Responding

```bash
# Check if running
ssh gpu-server "cd /opt/aifood && docker compose ps llm-gateway"

# Check logs for errors
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep ERROR"

# Rebuild and restart
ssh gpu-server "cd /opt/aifood && git pull && docker compose build llm-gateway && docker compose up -d llm-gateway"
```

---

## 📊 Production Services

| Service | Port | Status Check |
|---------|------|--------------|
| **LLM Gateway** | 9000 | `curl http://localhost:9000/health` |
| **Redis** | 6379 | `docker exec aifood-redis redis-cli ping` |
| **OpenClaw Gateway** | 18789 | `systemctl status openclaw-gateway` |
| **PostgreSQL** | 5433 | `psql -U aifood -d aifood -p 5433 -c "SELECT 1"` |
| **Ollama** | 8000 | `ollama ps` |

---

## 🔐 Current Production Configuration (2026-03-04)

**Gemini API Key**: `AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs`
**Model**: `google/gemini-2.5-flash`
**Telegram Bot**: @LenoxAI_bot
**Server**: 199.247.7.186 (gpu-server)

---

## 🥗 AiFood Plugin Commands

**Telegram Bot**: @LenoxAI_bot

### Available Tools (7 total)

| Tool | Description | Example |
|------|-------------|---------|
| `log_food` | Log food manually | "Съел 2 яйца на завтрак" |
| `log_food_from_photo` | Scan nutrition label | [Send photo of label] |
| `confirm_food_from_photo` | Confirm scanned item | "подтвердить 150г" |
| `daily_nutrition_report` | Daily KBJU report | "Покажи отчёт" |
| `set_nutrition_goals` | Set daily targets | "Цель: 2000 ккал, 150г белка" |
| `view_nutrition_profile` | View profile & progress | "Мой профиль" |
| `delete_food_entry` | Delete log entry | "Удали запись #5" |

### Quick Commands

```bash
# View help
/aifood

# Log food
"Съел 2 яйца и овсянку на завтрак"

# Daily report
"Покажи отчёт за сегодня"

# View profile with goals
"Мой профиль"

# Set goals
"Установи цель: 2000 ккал, 150г белка, 250г углеводов"

# Delete entry (get ID from report first)
"Удали запись #123"
```

---

## 📞 Support

- **Detailed Configs**: [OPENCLAW_CONFIG.md](OPENCLAW_CONFIG.md)
- **Deployment Status**: [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)
- **GitHub**: https://github.com/San2k/aifood
- **SSH Access**: `ssh gpu-server`

---

## 🎯 Common Workflows

### Deploy New Code
```bash
# On server
ssh gpu-server "cd /opt/aifood && git pull origin main"
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway"
ssh gpu-server "cd /opt/aifood && docker compose up -d llm-gateway"
```

### Check All Services Status
```bash
ssh gpu-server "systemctl status openclaw-gateway --no-pager | head -5"
ssh gpu-server "cd /opt/aifood && docker compose ps"
ssh gpu-server "curl -s http://localhost:9000/health"
```

### Backup Configuration
```bash
ssh gpu-server "tar -czf ~/openclaw-backup-$(date +%Y%m%d).tar.gz \
  ~/.openclaw/openclaw.json \
  ~/.openclaw/auth-profiles.json \
  ~/.openclaw/agents/main/agent/auth-profiles.json"
```

### Monitor Logs (All Services)
```bash
# OpenClaw
ssh gpu-server "journalctl -u openclaw-gateway -f"

# LLM Gateway
ssh gpu-server "cd /opt/aifood && docker compose logs -f llm-gateway"

# GPU
ssh gpu-server "watch -n 1 nvidia-smi"
```

---

**Last Updated**: 2026-03-04 06:32 UTC
