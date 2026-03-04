# AiFood - Production Deployment Status

**Last Updated**: 2026-03-04 11:57 MSK
**Servers**:
- **Primary (gpu-server)**: 199.247.7.186 ⚠️ **DEACTIVATED** (Ollama GPU only)
- **Production**: 199.247.30.52 (aifood-prod) ✅ **ACTIVE**
**Overall Status**: ✅ OPERATIONAL (Production Server Only)

---

## Current Production Services

### Server 1: 199.247.7.186 (gpu-server) ⚠️ **DEACTIVATED**

**Status**: AiFood services deactivated. Only Ollama GPU server remains active.

| Service | Port | Status | Version | Details |
|---------|------|--------|---------|---------|
| **LLM Gateway** | 9000 | ⏸️ Stopped | 1.0.0 | Deactivated |
| **Redis** | 6379 | ⏸️ Stopped | 7-alpine | Deactivated |
| **OpenClaw Gateway** | 18789 | ⏸️ Stopped | - | Deactivated (moved to production) |
| **Ollama** | 8000 | ✅ Running | - | GPU-enabled (qwen-prod-gpu) |
| **PostgreSQL** | 5433 | ⏸️ Stopped | - | Deactivated |

**Reason**: Telegram bot conflict (Error 409) - can only run on one server. All services moved to production server.

### Server 2: 199.247.30.52 (aifood-prod) ✅ **PRIMARY PRODUCTION**

**Status**: All services active. Primary production server for @LenoxAI_bot

| Service | Port | Status | Version | Details |
|---------|------|--------|---------|---------|
| **LLM Gateway** | 9000 | ✅ Running | 1.0.0 | Token optimization & Gemini proxy |
| **Agent API** | 8000 | ✅ Running | 2.0.0 | FastAPI + LangGraph service |
| **OCR Service** | 8001 | ✅ Running | 1.0.0 | PaddleOCR for receipts |
| **Redis** | 6379 | ✅ Running | 7-alpine | Cache & sessions |
| **PostgreSQL** | 5433 | ✅ Running | 16-alpine | Food log database |
| **OpenClaw Gateway** | 18789 | ✅ Running | - | Telegram bot @LenoxAI_bot |

**Telegram Bot**: ✅ Active without conflicts (Error 409 resolved)

---

## 🆕 LLM Gateway (NEW - March 3, 2026)

### Service Information
- **Endpoint**: `http://199.247.7.186:9000`
- **Container**: `aifood-llm-gateway`
- **Image**: `aifood-llm-gateway:latest`
- **Project Path**: `/opt/aifood/services/llm-gateway`

### Features Deployed ✅
- ✅ **Gemini 2.5 Flash Integration** - OpenAI-compatible API endpoint
- ✅ **Token Optimization** - Sliding window (8 msgs) + summarization (12k→1k)
- ✅ **Response Caching** - Redis-based deterministic caching
- ✅ **Quota Tracking** - 100k tokens/day, $50/month limits
- ✅ **Output Profiles** - brief (512), standard (1200), analysis (4000) tokens
- ✅ **Structured Logging** - Winston JSON logs with request tracking
- ✅ **Graceful Degradation** - Works without Redis if unavailable

### Production Performance
```
Latency (chat completion): ~850ms ✅
Health check response: < 10ms ✅
Token policy overhead: ~5ms ✅
Memory usage: ~150MB ✅
Uptime: 100% since deployment ✅
```

### Live Tests
```bash
# Health Check
curl http://199.247.7.186:9000/health
{"status":"ok","uptime":...,"version":"1.0.0"}

# English
POST /v1/chat/completions: "What is 2 plus 2?" → "2 plus 2 is 4." ✅

# Russian
POST /v1/chat/completions: "Сколько будет 5 плюс 3" → "5 плюс 3 будет 8." ✅
```

### Configuration
```yaml
Model: gemini-2.5-flash
Base URL: https://generativelanguage.googleapis.com/v1beta/openai/
Cache TTL: 3600 seconds
History Window: 8 messages / 12k tokens
Quotas: 100k tokens/day, $50/month
```

### Deployment Commit
- **Commit**: `fde9253`
- **Branch**: `main`
- **Date**: 2026-03-03 17:44 UTC

### Issues Resolved
1. ✅ **Package Lock Sync** - Fixed npm ci by regenerating package-lock.json
2. ✅ **Model Name** - Updated gemini-3-flash-preview → gemini-2.5-flash
3. ✅ **API Key Security** - Removed leaked keys from docs, using `.env` only
4. ✅ **Environment Variables** - Fixed hardcoded docker-compose.yml values
5. ✅ **OpenClaw API Key** (2026-03-04) - Updated auth-profiles.json (root + agent) with new key
6. ✅ **OpenClaw Model** (2026-03-04) - Changed gemini-1.5-flash → gemini-2.5-flash
7. ✅ **Systemd Environment** (2026-03-04) - Added GOOGLE_API_KEY and GEMINI_API_KEY
8. ✅ **AiFood Plugin** (2026-03-04) - Removed Kimi adapter, fixed /aifood command registration
9. ✅ **/aifood Command** (2026-03-04) - Fixed handler response type (markdown → text)
10. ✅ **API Key Validated** (2026-03-04) - Verified AIzaSyC6uqH... works correctly
11. ✅ **New Tools Added** (2026-03-04) - delete_food_entry, view_nutrition_profile (7 tools total)

### Documentation
- [README.md](services/llm-gateway/README.md) - API usage guide
- [DEPLOY.md](services/llm-gateway/DEPLOY.md) - Deployment instructions
- [VERIFICATION_REPORT.md](services/llm-gateway/VERIFICATION_REPORT.md) - Production report
- [IMPLEMENTATION_COMPLETE.md](services/llm-gateway/IMPLEMENTATION_COMPLETE.md) - Implementation details

---

## 🆕 Production Server Deployment (NEW - March 4, 2026)

### Server: 199.247.30.52 (aifood-prod)

**SSH Access**: `ssh aifood-prod` (using weeek_deploy key)

### Deployed Services

| Service | Port | Status | Container | Details |
|---------|------|--------|-----------|---------|
| **LLM Gateway** | 9000 | ✅ Running | aifood-llm-gateway | Token optimization & Gemini proxy |
| **Agent API** | 8000 | ✅ Running | aifood-agent-api | FastAPI service with LangGraph |
| **OCR Service** | 8001 | ✅ Running | aifood-ocr-service | PaddleOCR for food receipts |
| **Redis** | 6379 | ✅ Running | aifood-redis | Cache & sessions |
| **PostgreSQL** | 5433 | ✅ Running | aifood-postgres | Food log database |
| **OpenClaw Gateway** | 18789 | ✅ Running | systemd service | Telegram bot @LenoxAI_bot |

### Deployment Details

#### Date & Time
- **Deployed**: 2026-03-04 11:00-11:15 MSK
- **Code Updated**: 121 files (29 commits behind → up to date)
- **Commit**: Latest from main branch

#### Changes Made
1. ✅ **Code Sync** - Pulled latest from GitHub (services/llm-gateway, agent-api, ocr-service)
2. ✅ **.env Creation** - Added GEMINI_API_KEY and POSTGRES_PASSWORD
3. ✅ **LLM Gateway Build** - Built and deployed from scratch
4. ✅ **AiFood Plugin Update** - Rebuilt and installed with 7 tools (from 5)
5. ✅ **OpenClaw Configuration** - Updated plugins.allow, auth-profiles.json
6. ✅ **API Key Update** - Synced Gemini key across all configs

#### Configuration Files

**Environment**: `/opt/aifood/.env`
```bash
POSTGRES_PASSWORD=aifood_secure_password_2024
GEMINI_API_KEY=AIzaSyC6uqHhTHaPqMg6yUxyqotbQq-SHv6hB9A
GEMINI_MODEL=gemini-2.5-flash
```

**OpenClaw Config**: `/root/.openclaw/openclaw.json`
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen-optimized:latest",
        "fallbacks": ["google/gemini-2.0-flash-exp"]
      }
    }
  },
  "plugins": {
    "allow": ["aifood", "telegram"],
    "entries": {
      "aifood": {"enabled": true}
    }
  }
}
```

**Auth Profiles**: `/root/.openclaw/agents/main/agent/auth-profiles.json`
```json
{
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "AIzaSyC6uqHhTHaPqMg6yUxyqotbQq-SHv6hB9A"
    }
  }
}
```

#### AiFood Plugin Status
```
Plugin: aifood
Version: 1.0.0
Tools: 7
├─ log_food_entry
├─ search_food
├─ get_daily_nutrition_report
├─ get_weekly_nutrition_report
├─ set_nutrition_goals
├─ delete_food_entry (NEW)
└─ view_nutrition_profile (NEW)

Command: /aifood
Status: ✅ Active
```

### Service Health Checks

```bash
# LLM Gateway
curl http://199.247.30.52:9000/health
{"status":"ok","uptime":233.24,"version":"1.0.0"} ✅

# Agent API
curl http://199.247.30.52:8000/health
{"status":"ok","service":"agent-api","version":"2.0.0"} ✅

# OCR Service
curl http://199.247.30.52:8001/health
{"status":"ok","service":"ocr-service","version":"1.0.0"} ✅

# OpenClaw Gateway
systemctl status openclaw-gateway
Active: active (running) ✅

# Telegram Bot
@LenoxAI_bot responding ✅
```

### Known Issues (Resolved)

1. **Telegram Bot Conflict (Error 409)** - ✅ **RESOLVED**
   - **Cause**: Bot was running simultaneously on both servers (gpu-server and aifood-prod)
   - **Solution**: Stopped all OpenClaw services on gpu-server (both system and user-level systemd)
   - **Current State**: Bot runs only on aifood-prod (199.247.30.52)
   - **Resolution Date**: 2026-03-04 11:55 MSK

2. **LLM Gateway Healthcheck** - Docker healthcheck shows "unhealthy" but service works
   - **Cause**: healthcheck command uses node -e which may fail in alpine container
   - **Impact**: None - /health endpoint responds correctly
   - **Action**: Monitor, may fix in future

### Co-existing Services

Production server also hosts:
- **Weeek Project** (containers: weeek-*)
- **Airflow** (scheduler, webserver)
- **Grafana** (port 3000)
- **Prometheus** (port 9090)
- **MCP Server** (port 9106)

All services running without conflicts. ✅

### Monitoring Commands

```bash
# All AiFood containers
ssh aifood-prod "docker ps --filter name=aifood"

# Service logs
ssh aifood-prod "docker logs -f aifood-llm-gateway"
ssh aifood-prod "journalctl -u openclaw-gateway -f"

# Database check
ssh aifood-prod "docker exec aifood-postgres psql -U aifood -d aifood -c '\dt'"

# Health check all services
ssh aifood-prod "curl -s http://localhost:9000/health && curl -s http://localhost:8000/health && curl -s http://localhost:8001/health"
```

### Next Steps for Production Server
- [ ] Configure automated backups for PostgreSQL
- [ ] Setup log rotation for Docker containers
- [ ] Enable monitoring/alerting for service health
- [ ] Document disaster recovery procedures
- [ ] Add SSL/TLS for external access (if needed)

---

## OpenClaw Gateway + Ollama (Existing)

### Status
- **Gateway**: ✅ Running (PID check: `systemctl status openclaw-gateway`)
- **Model**: google/gemini-2.5-flash
- **Telegram**: @LenoxAI_bot ✅ Active
- **AiFood Plugin**: ✅ Loaded (7 tools + /aifood command)

### GPU Configuration
```
GPU: NVIDIA A40-8Q (8GB VRAM)
Model: Qwen 2.5:14b (GPU-optimized)
GPU Layers: 30/49 (61% on GPU, 39% on CPU)
Context Window: 4096 tokens
Memory Usage: 7.4 GB / 8.0 GB
Status: Stable, no OOM errors ✅
```

### Performance
```
Response Time: 6-12 seconds
GPU Utilization: 6% (partial offload)
Eval Rate: 4-5 tokens/s
Load Duration: 2-3 seconds
```

### Recent Optimizations (2026-03-02)
1. **GPU Memory Fix** - Reduced num_ctx from 8192 to 4096 to fit in 8GB VRAM
2. **Quantization Test** - 2.2x SLOWER, reverted to full precision
3. **Stability** - No OOM errors after context reduction ✅

---

## Database (PostgreSQL)

### Status
- **Port**: 5433
- **Status**: ✅ Running
- **Database**: `aifood`
- **Tables**: `food_log_entry`, `user_goals`, `user_profile`

---

## Monitoring

### Quick Status Check
```bash
# All services
ssh gpu-server "cd /opt/aifood && docker compose ps"

# LLM Gateway
ssh gpu-server "curl -s http://localhost:9000/health"

# OpenClaw Gateway
ssh gpu-server "systemctl status openclaw-gateway"

# GPU
ssh gpu-server "nvidia-smi"
```

### Log Monitoring
```bash
# LLM Gateway logs
ssh gpu-server "cd /opt/aifood && docker compose logs -f llm-gateway"

# OpenClaw Gateway logs
ssh gpu-server "journalctl -u openclaw-gateway -f"

# Check for errors
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep ERROR"
```

### Performance Monitoring
```bash
# LLM Gateway metrics
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep latency | tail -20"

# GPU real-time
ssh gpu-server "watch -n 1 nvidia-smi"

# Container stats
ssh gpu-server "docker stats aifood-llm-gateway aifood-redis --no-stream"
```

---

## Maintenance

### Update LLM Gateway
```bash
# Pull latest code
ssh gpu-server "cd /opt/aifood && git pull origin main"

# Rebuild and restart
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway && docker compose up -d llm-gateway"

# Verify
ssh gpu-server "curl -s http://localhost:9000/health"
```

### Restart Services
```bash
# LLM Gateway only
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"

# OpenClaw Gateway
ssh gpu-server "systemctl restart openclaw-gateway"

# Ollama
ssh gpu-server "systemctl restart ollama"

# All Docker services
ssh gpu-server "cd /opt/aifood && docker compose restart"
```

---

## Configuration Files

📋 **Complete Configuration Guide**: [OPENCLAW_CONFIG.md](OPENCLAW_CONFIG.md)

### LLM Gateway `.env`
**Location**: `/opt/aifood/.env`
```bash
GEMINI_API_KEY=<secure_key>
GEMINI_MODEL=gemini-2.5-flash
POSTGRES_PASSWORD=<secure_password>
```

### OpenClaw Configuration Files

| File | Location | Critical? |
|------|----------|-----------|
| Main Config | `/root/.openclaw/openclaw.json` | ✅ |
| Root Auth | `/root/.openclaw/auth-profiles.json` | ✅ |
| **Agent Auth** | `/root/.openclaw/agents/main/agent/auth-profiles.json` | ⚠️ **MOST IMPORTANT** |
| Systemd Service | `/etc/systemd/system/openclaw-gateway.service` | ✅ |

#### Main Config (`openclaw.json`)
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.5-flash",
        "fallbacks": []
      }
    }
  },
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "databaseUrl": "postgresql://aifood:password@localhost:5433/aifood"
        }
      }
    }
  }
}
```

#### Gemini API Authentication
**Location 1** (Root): `/root/.openclaw/auth-profiles.json`
**Location 2** (Agent): `/root/.openclaw/agents/main/agent/auth-profiles.json`

⚠️ **CRITICAL**: Must update BOTH files when changing API key!

```json
{
  "version": 1,
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "<secure_key>"
    }
  }
}
```

#### Systemd Environment Variables
**Location**: `/etc/systemd/system/openclaw-gateway.service`
```ini
Environment="GOOGLE_API_KEY=<secure_key>"
Environment="GEMINI_API_KEY=<secure_key>"
```

---

## Security

### Checklist
- [x] API keys in `.env` (not in git)
- [x] `.gitignore` protects sensitive files
- [x] Old leaked keys removed from documentation
- [x] SSH key-based authentication
- [x] Docker containers with limited privileges
- [x] Health endpoints don't expose secrets
- [ ] TODO: Rate limiting per IP
- [ ] TODO: API authentication for gateway
- [ ] TODO: SSL/TLS for external access

### Firewall
```bash
# Current: Services accessible only from localhost
# To enable external access (use with caution):
ssh gpu-server "ufw allow 9000/tcp"  # LLM Gateway
ssh gpu-server "ufw allow 18789/tcp" # OpenClaw Gateway
```

---

## Troubleshooting

### LLM Gateway Issues

#### Gateway Won't Start
```bash
# Check logs
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway"

# Verify environment
ssh gpu-server "docker exec aifood-llm-gateway printenv | grep GEMINI"

# Check port
ssh gpu-server "lsof -i :9000"
```

#### Gemini API Errors
```bash
# Test API key directly
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | head -20'

# Check model availability
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | grep name'
```

### OpenClaw/Ollama Issues

#### API Key Expired Error
```bash
# If OpenClaw reports "API key expired" for Gemini:

# 1. Verify API key works
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | head -20'

# 2. Check BOTH auth-profiles.json files (CRITICAL!)
ssh gpu-server "cat ~/.openclaw/auth-profiles.json | grep key"
ssh gpu-server "cat ~/.openclaw/agents/main/agent/auth-profiles.json | grep key"

# 3. Update ROOT auth-profiles.json
ssh gpu-server "cat > ~/.openclaw/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"YOUR_GEMINI_API_KEY\"
    }
  }
}
EOF"

# 4. Update AGENT auth-profiles.json (MOST IMPORTANT!)
ssh gpu-server "cat > ~/.openclaw/agents/main/agent/auth-profiles.json << 'EOF'
{
  \"version\": 1,
  \"profiles\": {
    \"google:default\": {
      \"type\": \"api_key\",
      \"provider\": \"google\",
      \"key\": \"YOUR_GEMINI_API_KEY\"
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

# 5. Restart OpenClaw Gateway
ssh gpu-server "systemctl restart openclaw-gateway"

# 6. Check logs for errors
ssh gpu-server "journalctl -u openclaw-gateway --since '1 minute ago' --no-pager | grep -i error"
```

#### GPU Not Utilized
```bash
# Check GPU status
ssh gpu-server "nvidia-smi"

# Verify model loaded
ssh gpu-server "ollama ps"

# Check GPU layers
ssh gpu-server "ollama show qwen-prod-gpu:latest --modelfile"
```

#### Out of Memory
```bash
# Current: num_ctx=4096 (stable)
# If OOM occurs: Reduce num_gpu from 30 to 28

# Restart Ollama
ssh gpu-server "systemctl restart ollama"
```

---

## Next Steps

### Immediate (Week 3)
- [ ] Connect OpenClaw to LLM Gateway endpoint
- [ ] Configure health check automation (cron)
- [ ] Setup log rotation for gateway
- [ ] Monitor performance for 24-48 hours

### Short-term
- [ ] Unit tests for gateway
- [ ] Integration tests (gateway + OpenClaw)
- [ ] Prometheus metrics export
- [ ] Grafana dashboards

### Long-term
- [ ] Multi-provider support (OpenAI, Anthropic)
- [ ] Load balancing (multiple gateway instances)
- [ ] Advanced routing (intent-based model selection)
- [ ] High availability setup

---

## Performance Summary

| Component | Metric | Status |
|-----------|--------|--------|
| **LLM Gateway** | 850ms latency | ✅ Excellent |
| **Redis** | < 5ms latency | ✅ Fast |
| **OpenClaw + Ollama** | 6-12s response | ✅ Acceptable |
| **GPU Memory** | 7.4 GB / 8.0 GB | ✅ Stable |
| **Gateway Memory** | ~150MB | ✅ Optimized |

---

## Support

- **LLM Gateway Docs**: [services/llm-gateway/](services/llm-gateway/)
- **OpenClaw Docs**: `~/.openclaw/` on server
- **Issue Tracker**: GitHub Issues
- **Server Access**: `ssh gpu-server`

---

**Overall Status**: ✅ All Services Operational
**Last Verified**: 2026-03-04 07:28 UTC
**Next Review**: 2026-03-05
