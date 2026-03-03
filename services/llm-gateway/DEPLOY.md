# LLM Gateway - Production Deployment Guide

## Server Information

- **Server IP**: 199.247.7.186
- **SSH Alias**: `gpu-server`
- **User**: root
- **Project Path**: `/opt/aifood`
- **Gateway Port**: 9000
- **Redis Port**: 6379

## Prerequisites

На сервере должно быть установлено:
- ✅ Docker (verified)
- ✅ Docker Compose v5.0.2+ (verified)
- ✅ Git (verified)
- ✅ SSH access configured

## Quick Deployment

```bash
# SSH to server
ssh gpu-server

# Navigate to project
cd /opt/aifood

# Pull latest code
git pull origin main

# Configure environment (do this once)
cat > .env << 'EOF'
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
POSTGRES_PASSWORD=your_secure_password
EOF

# Build and start services
docker compose build llm-gateway
docker compose up -d llm-gateway redis

# Verify deployment
docker compose ps
curl http://localhost:9000/health
```

## Detailed Deployment Steps

### 1. SSH Access Setup (First Time Only)

На локальной машине:
```bash
# Verify SSH access
ssh gpu-server

# If key not found, add to ~/.ssh/config:
Host gpu-server
    HostName 199.247.7.186
    User root
    IdentityFile ~/.ssh/weeek_deploy
```

### 2. Pull Latest Code

```bash
ssh gpu-server "cd /opt/aifood && git pull origin main"
```

### 3. Configure Environment Variables

**IMPORTANT**: Никогда не публикуйте `.env` файл в git!

```bash
ssh gpu-server "cd /opt/aifood && cat > .env << 'EOF'
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_from_https://aistudio.google.com/app/apikey
GEMINI_MODEL=gemini-2.5-flash

# Database
POSTGRES_PASSWORD=your_secure_password_here
EOF
"
```

**Доступные модели Gemini**:
- `gemini-2.5-flash` (recommended) - Fast, efficient, supports 1M tokens
- `gemini-2.5-pro` - More powerful, slower
- `gemini-2.0-flash` - Previous generation

**Проверить валидность API ключа**:
```bash
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY" | head -20'
```

### 4. Build Docker Image

```bash
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway"
```

Ожидаемый вывод:
```
✓ Multi-stage build successful
✓ TypeScript compilation: No errors
✓ Dependencies installed: 494 packages
✓ Build time: ~70 seconds
```

### 5. Start Services

```bash
# Start gateway + redis
ssh gpu-server "cd /opt/aifood && docker compose up -d llm-gateway redis"

# Verify status
ssh gpu-server "cd /opt/aifood && docker compose ps"
```

Ожидаемый статус:
```
NAME                 STATUS                   PORTS
aifood-llm-gateway   Up (healthy)            0.0.0.0:9000->9000/tcp
aifood-redis         Up (healthy)            0.0.0.0:6379->6379/tcp
```

### 6. Verification

#### Health Check
```bash
ssh gpu-server "curl -s http://localhost:9000/health"

# Expected:
# {"status":"ok","uptime":...,"timestamp":...,"version":"1.0.0"}
```

#### Chat Completion Test
```bash
ssh gpu-server 'curl -s -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"gemini-2.5-flash\",\"messages\":[{\"role\":\"user\",\"content\":\"Test message\"}],\"max_tokens\":50}"'
```

Expected response:
```json
{
  "choices": [{
    "finish_reason": "stop",
    "message": {
      "content": "...",
      "role": "assistant"
    }
  }],
  "usage": {
    "prompt_tokens": ...,
    "completion_tokens": ...,
    "total_tokens": ...
  }
}
```

#### Check Logs
```bash
ssh gpu-server "cd /opt/aifood && docker compose logs -f llm-gateway"

# Look for:
# ✓ "server_start" - Gateway listening on 0.0.0.0:9000
# ✓ "cache_connected" - Redis connection established
# ✓ "quota_redis_connected" - Quota service ready
# ✓ "token_counter_init" - Token counter initialized
```

## Configuration Reference

### Docker Compose Environment

Конфигурация в `docker-compose.yml`:

```yaml
llm-gateway:
  environment:
    # Server
    GATEWAY_PORT: 9000
    GATEWAY_HOST: 0.0.0.0

    # Gemini API (from .env)
    GEMINI_API_KEY: ${GEMINI_API_KEY}
    GEMINI_MODEL: ${GEMINI_MODEL:-gemini-2.5-flash}
    GEMINI_BASE_URL: https://generativelanguage.googleapis.com/v1beta/openai/
    GEMINI_TIMEOUT: 60000
    GEMINI_RETRIES: 3

    # Redis
    REDIS_URL: redis://redis:6379/1

    # Token Policy
    HISTORY_WINDOW_TOKENS: 12000
    HISTORY_WINDOW_MESSAGES: 8
    SUMMARY_TRIGGER_TOKENS: 12000
    SUMMARY_TARGET_TOKENS: 1000
    RAG_BUDGET_TOKENS: 2000

    # Cache
    CACHE_ENABLED: "true"
    CACHE_TTL: 3600

    # Quotas
    QUOTA_DAILY_TOKENS: 100000
    QUOTA_MONTHLY_USD: 50

    # Observability
    LOG_LEVEL: info
    METRICS_ENABLED: "false"
```

### Model Routing

Gateway поддерживает логические имена моделей:

| Model Name | Actual Model | Max Tokens | Description |
|------------|--------------|------------|-------------|
| `brief` | gemini-2.5-flash | 512 | Короткие ответы |
| `standard` | gemini-2.5-flash | 1200 | Обычные диалоги (по умолчанию) |
| `analysis` | gemini-2.5-flash | 4000 | Детальный анализ |
| `gemini-2.5-flash` | gemini-2.5-flash | custom | Прямой доступ к модели |

## Maintenance

### Restart Services

```bash
# Restart gateway only
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"

# Restart all services
ssh gpu-server "cd /opt/aifood && docker compose restart"
```

### Update Deployment

```bash
# Pull latest code
ssh gpu-server "cd /opt/aifood && git pull origin main"

# Rebuild and restart
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway && docker compose up -d llm-gateway"
```

### View Logs

```bash
# Real-time logs
ssh gpu-server "cd /opt/aifood && docker compose logs -f llm-gateway"

# Last 100 lines
ssh gpu-server "cd /opt/aifood && docker compose logs --tail=100 llm-gateway"

# Filter for errors
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep ERROR"

# Token optimization monitoring
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep -E 'token_policy|history_optimization'"
```

### Check Resource Usage

```bash
# Container stats
ssh gpu-server "docker stats aifood-llm-gateway aifood-redis --no-stream"

# Disk usage
ssh gpu-server "cd /opt/aifood && docker compose ps --format json | jq"
```

## Troubleshooting

### Gateway Won't Start

```bash
# Check if port 9000 is already in use
ssh gpu-server "lsof -i :9000"

# Check Docker logs for errors
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway"

# Verify environment variables
ssh gpu-server "docker exec aifood-llm-gateway printenv | grep GEMINI"
```

### Redis Connection Errors

Gateway работает без Redis (graceful degradation), но с ограниченной функциональностью:
- ❌ No cache
- ❌ No quota tracking
- ✅ History optimization works
- ✅ Gemini requests work

**Fix**:
```bash
# Ensure Redis is running
ssh gpu-server "cd /opt/aifood && docker compose up -d redis"

# Check Redis health
ssh gpu-server "docker exec aifood-redis redis-cli ping"
# Should return: PONG

# Restart gateway
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"
```

### Gemini API Errors

#### Error: API key expired
```bash
# Get new API key from: https://aistudio.google.com/app/apikey

# Update .env
ssh gpu-server "cd /opt/aifood && nano .env"

# Restart gateway
ssh gpu-server "cd /opt/aifood && docker compose restart llm-gateway"
```

#### Error: Model not found (404)
```bash
# Check available models
ssh gpu-server 'curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | grep name'

# Update GEMINI_MODEL in .env to valid model (e.g., gemini-2.5-flash)
ssh gpu-server "cd /opt/aifood && nano .env"

# Recreate container
ssh gpu-server "cd /opt/aifood && docker compose down llm-gateway && docker compose up -d llm-gateway"
```

#### Error: Rate limit exceeded (429)
Gateway имеет встроенный retry logic с exponential backoff. Если проблема персистит:
```bash
# Check quota service logs
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep quota"

# Adjust quota limits in docker-compose.yml if needed
```

### Build Failures

#### Error: package-lock.json out of sync
```bash
# На локальной машине:
cd services/llm-gateway
npm install
git add package-lock.json
git commit -m "fix: Update package-lock.json"
git push origin main

# На сервере:
ssh gpu-server "cd /opt/aifood && git pull origin main && docker compose build llm-gateway"
```

#### Error: TypeScript compilation errors
```bash
# Check build logs
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway 2>&1 | grep error"

# Usually fixed by pulling latest code
ssh gpu-server "cd /opt/aifood && git pull origin main"
```

## Monitoring

### Health Check Automation

Добавить в cron для автоматического перезапуска при падении:

```bash
ssh gpu-server "crontab -e"

# Add:
*/5 * * * * curl -f http://localhost:9000/health > /dev/null 2>&1 || docker compose -f /opt/aifood/docker-compose.yml restart llm-gateway
```

### Log Rotation

Setup logrotate для автоматической ротации логов:

```bash
ssh gpu-server "cat > /etc/logrotate.d/llm-gateway << 'EOF'
/opt/aifood/services/llm-gateway/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
"
```

### Performance Monitoring

```bash
# Check response times
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep latency | tail -20"

# Cache hit rate
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep cache_hit"

# Token usage statistics
ssh gpu-server "cd /opt/aifood && docker compose logs llm-gateway | grep token_policy_complete | tail -10"
```

## Rollback Procedure

Если новая версия не работает:

```bash
# Stop services
ssh gpu-server "cd /opt/aifood && docker compose stop llm-gateway"

# Remove container
ssh gpu-server "cd /opt/aifood && docker compose rm -f llm-gateway"

# Revert to previous commit
ssh gpu-server "cd /opt/aifood && git log --oneline -5"  # Find previous commit
ssh gpu-server "cd /opt/aifood && git reset --hard COMMIT_HASH"

# Rebuild and restart
ssh gpu-server "cd /opt/aifood && docker compose build llm-gateway && docker compose up -d llm-gateway"
```

## Firewall Configuration

Если нужен внешний доступ к Gateway:

```bash
# Allow port 9000 (if using ufw)
ssh gpu-server "ufw allow 9000/tcp"

# Or if using firewalld
ssh gpu-server "firewall-cmd --permanent --add-port=9000/tcp && firewall-cmd --reload"
```

**⚠️ Security Warning**: Открытие порта 9000 сделает Gateway доступным извне. Рекомендуется:
- Использовать reverse proxy (nginx)
- Добавить authentication middleware
- Настроить rate limiting

## Security Checklist

- [x] API key в `.env` (не в git)
- [x] `.gitignore` защищает `.env`
- [x] Старые leaked keys удалены из документации
- [x] Docker volumes с ограниченными правами
- [x] Health check не раскрывает чувствительную информацию
- [ ] TODO: Rate limiting per IP
- [ ] TODO: API authentication tokens
- [ ] TODO: SSL/TLS certificate (если внешний доступ)

## Production Checklist

После деплоя проверьте:

- [ ] Gateway отвечает на health check
- [ ] Chat completions работают (English + Russian)
- [ ] Redis подключен (проверить логи - нет ECONNREFUSED)
- [ ] History optimization срабатывает на длинных диалогах
- [ ] Логи пишутся в `./services/llm-gateway/logs/`
- [ ] Quota tracking работает (если Redis доступен)
- [ ] Token policy применяется (см. логи)
- [ ] Latency < 2 секунд для обычных запросов
- [ ] Memory usage стабилен (~150MB)
- [ ] No memory leaks (мониторить несколько часов)

## Support

При проблемах:
1. Проверьте логи: `docker compose logs llm-gateway`
2. Проверьте health check: `curl http://localhost:9000/health`
3. Проверьте документацию: [README.md](README.md)
4. Проверьте статус реализации: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)

---

**Last Updated**: 2026-03-03
**Production Server**: 199.247.7.186
**Status**: ✅ Deployed and Operational
