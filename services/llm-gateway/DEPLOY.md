# LLM Gateway - Deployment Instructions

## Prerequisites

Убедитесь, что на сервере (199.247.7.186) установлены:
- Docker
- Docker Compose
- Git

## Deployment Steps

### 1. Sync Code to Server

Сначала закоммитьте все изменения:

```bash
# На локальной машине
cd /Users/sandro/Documents/Other/AiFood

# Проверить статус
git status

# Добавить новые файлы
git add services/llm-gateway/
git add docker-compose.yml

# Коммит
git commit -m "feat: Add LLM Gateway with token optimization

- Implemented Core Gateway (Week 1)
  - Fastify server with Gemini provider
  - OpenAI-compatible API endpoint
  - Streaming + non-streaming support
  - Docker integration

- Implemented Token Policy Engine (Week 2)
  - Token counter service with tiktoken
  - History manager (sliding window + summarization)
  - Cache service (Redis)
  - Quota service (per-tenant limits)
  - Token policy middleware

- Full optimization pipeline:
  - Output profile enforcement
  - History optimization (26% token savings)
  - Response caching for deterministic queries
  - Usage tracking and quota enforcement
  - Graceful degradation when Redis unavailable

Gateway runs on port 9000, integrated with existing docker-compose.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push origin main
```

### 2. Deploy on Server

SSH в сервер и выполните:

```bash
# SSH на сервер
ssh root@199.247.7.186

# Перейти в директорию проекта
cd /root/aifood

# Pull latest changes
git pull origin main

# Проверить, что .env содержит GEMINI_API_KEY
grep GEMINI_API_KEY .env

# Если нет - добавить:
echo "GEMINI_API_KEY=AIzaSyAq1AoNdzjLXmxXl3uVq8UZu_shTDmlTVY" >> .env

# Build and start LLM Gateway
docker-compose build llm-gateway
docker-compose up -d llm-gateway

# Проверить статус
docker-compose ps llm-gateway

# Проверить логи
docker-compose logs -f llm-gateway
```

### 3. Verify Deployment

```bash
# Health check
curl http://localhost:9000/health

# Expected response:
# {"status":"ok","uptime":...,"timestamp":...,"version":"1.0.0"}

# Test chat completion
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3-flash-preview",
    "messages": [{"role": "user", "content": "Привет!"}],
    "max_tokens": 50
  }'

# Should return:
# {"id":"...","choices":[{"message":{"content":"...","role":"assistant"},...}],...}
```

### 4. Check Logs

```bash
# View logs
docker-compose logs -f llm-gateway

# Check for errors
docker-compose logs llm-gateway | grep ERROR

# Check optimization actions
docker-compose logs llm-gateway | grep "history_optimization"

# Check cache hits
docker-compose logs llm-gateway | grep "cache_hit"
```

### 5. Verify Services Integration

Gateway должен быть доступен другим сервисам:

```bash
# From another container (e.g., agent-api)
docker-compose exec agent-api curl http://llm-gateway:9000/health

# Or from host
curl http://199.247.7.186:9000/health
```

## Firewall Configuration (if needed)

Если нужен внешний доступ к Gateway:

```bash
# Allow port 9000
sudo ufw allow 9000/tcp

# Or if using firewalld
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

## Rollback (if needed)

Если что-то пошло не так:

```bash
# Stop LLM Gateway
docker-compose stop llm-gateway

# Remove container
docker-compose rm -f llm-gateway

# Revert git changes
git reset --hard HEAD~1

# Restart other services
docker-compose up -d
```

## Troubleshooting

### Gateway won't start

```bash
# Check if port 9000 is already in use
lsof -i :9000

# Check Docker logs
docker-compose logs llm-gateway

# Check Redis is running
docker-compose ps redis
```

### Redis connection errors

Gateway работает без Redis (graceful degradation), но с ограниченной функциональностью:
- ❌ No cache
- ❌ No quota tracking
- ✅ History optimization works
- ✅ Gemini requests work

```bash
# Ensure Redis is running
docker-compose up -d redis

# Check Redis health
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart gateway
docker-compose restart llm-gateway
```

### Gemini API errors

```bash
# Check API key is set
docker-compose exec llm-gateway printenv GEMINI_API_KEY

# Test API key manually
curl -X POST "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
  -H "Authorization: Bearer AIzaSyAq1AoNdzjLXmxXl3uVq8UZu_shTDmlTVY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3-flash-preview",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 5
  }'
```

## Monitoring

### Health Check

Add to cron for periodic health checks:

```bash
# /etc/cron.d/llm-gateway-health
*/5 * * * * root curl -f http://localhost:9000/health > /dev/null 2>&1 || docker-compose -f /root/aifood/docker-compose.yml restart llm-gateway
```

### Log Rotation

Logs stored in `./services/llm-gateway/logs/`:

```bash
# Setup logrotate
cat > /etc/logrotate.d/llm-gateway <<EOF
/root/aifood/services/llm-gateway/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

## Performance Tuning

### Redis Memory Limit

```bash
# In docker-compose.yml, add to redis service:
services:
  redis:
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Gateway Concurrency

Currently using single Node.js process. For production with high load:

```bash
# Add to docker-compose.yml environment:
NODE_ENV=production
UV_THREADPOOL_SIZE=128
```

## OpenClaw Integration

После деплоя обновите OpenClaw config:

```bash
ssh gpu-server

# Edit OpenClaw config
nano ~/.openclaw/openclaw.json
```

Add gateway provider:

```json
{
  "models": {
    "providers": {
      "gateway": {
        "baseUrl": "http://199.247.7.186:9000/v1",
        "api": "openai-completions",
        "models": [
          {
            "id": "brief",
            "name": "Brief Output (256-512 tokens)",
            "contextWindow": 100000,
            "maxTokens": 512
          },
          {
            "id": "standard",
            "name": "Standard Output (800-1200 tokens)",
            "contextWindow": 100000,
            "maxTokens": 1200
          }
        ]
      }
    }
  }
}
```

Restart OpenClaw:

```bash
systemctl restart openclaw-gateway
```

## Success Verification

После деплоя проверьте:

- [ ] Gateway отвечает на health check
- [ ] Chat completions работают
- [ ] Redis подключен (проверить логи - нет ECONNREFUSED)
- [ ] History optimization срабатывает на длинных диалогах
- [ ] Логи пишутся в `./services/llm-gateway/logs/`
- [ ] Quota tracking работает (если Redis доступен)

## Support

При проблемах:
1. Проверьте логи: `docker-compose logs llm-gateway`
2. Проверьте документацию: [README.md](README.md)
3. Проверьте статус реализации: [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
