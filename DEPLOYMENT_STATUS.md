# AiFood - Production Deployment Status

**Last Updated**: 2026-03-04 07:20 UTC
**Server**: 199.247.7.186 (gpu-server)
**Overall Status**: ✅ OPERATIONAL

---

## Current Production Services

| Service | Port | Status | Version | Details |
|---------|------|--------|---------|---------|
| **LLM Gateway** | 9000 | ✅ Running | 1.0.0 | **NEW** - Production deployment complete |
| **Redis** | 6379 | ✅ Running | 7-alpine | Cache & quota tracking |
| **OpenClaw Gateway** | 18789 | ✅ Running | - | Telegram bot @LenoxAI_bot |
| **Ollama** | 8000 | ✅ Running | - | GPU-enabled (qwen-prod-gpu) |
| **PostgreSQL** | 5433 | ✅ Running | - | Food log database |

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

### Documentation
- [README.md](services/llm-gateway/README.md) - API usage guide
- [DEPLOY.md](services/llm-gateway/DEPLOY.md) - Deployment instructions
- [VERIFICATION_REPORT.md](services/llm-gateway/VERIFICATION_REPORT.md) - Production report
- [IMPLEMENTATION_COMPLETE.md](services/llm-gateway/IMPLEMENTATION_COMPLETE.md) - Implementation details

---

## OpenClaw Gateway + Ollama (Existing)

### Status
- **Gateway**: ✅ Running (PID check: `systemctl status openclaw-gateway`)
- **Model**: qwen-prod-gpu:latest (GPU-optimized)
- **Telegram**: @LenoxAI_bot ✅ Active
- **AiFood Plugin**: ✅ Loaded (5 tools)

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
**Last Verified**: 2026-03-04 07:20 UTC
**Next Review**: 2026-03-05
