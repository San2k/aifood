# Pre-Flight Checklist

Complete this checklist before starting the AI Nutrition Bot for the first time.

## ✅ 1. Environment Setup

### Docker Installation
- [ ] Docker Desktop is installed
- [ ] Docker is running (`docker --version`)
- [ ] Docker Compose is available (`docker-compose --version`)

### Project Files
- [ ] All project files are present
- [ ] No missing directories or files
- [ ] Scripts are executable (`chmod +x scripts/*.sh`)

---

## ✅ 2. API Credentials

### Telegram Bot Token
- [ ] Created bot via @BotFather on Telegram
- [ ] Copied bot token
- [ ] Token format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

**How to get**:
1. Open Telegram and search for @BotFather
2. Send: `/newbot`
3. Follow prompts to create bot
4. Copy token from response

### OpenAI API Key
- [ ] Have OpenAI account
- [ ] Created API key at platform.openai.com
- [ ] Have access to GPT-4 (required)
- [ ] Key format: `sk-...`

**Required models**:
- GPT-4 Turbo (for text parsing)
- GPT-4o (for photo OCR - Phase 2)

**Check access**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY" | grep gpt-4
```

### FatSecret API Credentials
- [ ] Created account at platform.fatsecret.com
- [ ] Created application
- [ ] Have Client ID and Client Secret
- [ ] OAuth2 credentials working

**How to get**:
1. Go to https://platform.fatsecret.com/
2. Sign up / Log in
3. Create new application
4. Copy Client ID and Client Secret

**Test credentials**:
```bash
# Test OAuth token fetch (replace with your credentials)
curl -X POST https://oauth.fatsecret.com/connect/token \
  -d "grant_type=client_credentials&scope=basic" \
  -u "CLIENT_ID:CLIENT_SECRET"
```

---

## ✅ 3. Environment Configuration

### Create .env file
- [ ] File exists: `/Users/sandro/Documents/Other/AiFood/.env`
- [ ] All required variables are set
- [ ] No placeholder values remaining
- [ ] No extra spaces or quotes

### Required Variables

Copy this template and fill in your actual values:

```bash
# === Database ===
DATABASE_URL=postgresql+asyncpg://nutrition_user:nutrition_password_2024@postgres:5432/nutrition_bot

# === Redis ===
REDIS_URL=redis://redis:6379

# === Telegram Bot ===
TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE

# === OpenAI ===
OPENAI_API_KEY=YOUR_ACTUAL_KEY_HERE
OPENAI_MODEL_TEXT=gpt-4-turbo-preview
OPENAI_MODEL_VISION=gpt-4o

# === FatSecret API ===
FATSECRET_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID_HERE
FATSECRET_CLIENT_SECRET=YOUR_ACTUAL_SECRET_HERE

# === Application Settings ===
AGENT_API_URL=http://agent-api:8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# === Conversation Settings ===
CONVERSATION_EXPIRE_SECONDS=3600
MAX_CLARIFICATIONS=5
```

### Verify .env file
```bash
# Check file exists
ls -la .env

# Check no placeholder values remain
grep "YOUR_ACTUAL" .env
# Should return nothing if all filled

# Check for common issues
grep "= " .env  # Should have no spaces after =
```

---

## ✅ 4. System Resources

### Docker Resources
- [ ] At least 4GB RAM allocated to Docker
- [ ] At least 10GB free disk space
- [ ] CPU: 2+ cores recommended

**Check Docker resources**:
- Docker Desktop → Settings → Resources

### Network Ports
- [ ] Port 5432 (PostgreSQL) is free
- [ ] Port 6379 (Redis) is free
- [ ] Port 8000 (Agent API) is free

**Check ports**:
```bash
# macOS/Linux
lsof -i :5432
lsof -i :6379
lsof -i :8000

# Should return nothing if ports are free
```

---

## ✅ 5. First Run Verification

### Build Images
```bash
cd /Users/sandro/Documents/Other/AiFood

# Build without starting
docker-compose build
```

**Expected**: All 3 services build successfully
- ✅ agent-api
- ✅ telegram-bot
- ✅ mcp-fatsecret

**Common issues**:
- Python package conflicts → Check requirements.txt versions
- Base image pull failures → Check internet connection

### Start Services
```bash
# Use startup script (recommended)
./scripts/startup.sh

# OR manual start
docker-compose up -d
sleep 10
docker-compose exec agent-api alembic upgrade head
```

**Expected output**:
```
Creating network "aifood_default" ...
Creating aifood_postgres_1 ...
Creating aifood_redis_1 ...
Creating aifood_agent-api_1 ...
Creating aifood_telegram-bot_1 ...
```

### Verify All Services Running
```bash
docker-compose ps
```

**Expected**: All services "Up"
```
NAME                   STATUS
postgres               Up (healthy)
redis                  Up (healthy)
agent-api              Up
telegram-bot           Up
```

### Check Logs for Errors
```bash
# Check each service
docker-compose logs agent-api | grep ERROR
docker-compose logs telegram-bot | grep ERROR
docker-compose logs postgres | grep ERROR
docker-compose logs redis | grep ERROR

# Should return nothing or only non-critical errors
```

---

## ✅ 6. Database Verification

### Check Migrations
```bash
docker-compose exec agent-api alembic current
```

**Expected**: Shows current migration version (e.g., `001 (head)`)

### Verify Tables
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c "\dt"
```

**Expected tables**:
- user_profile
- food_log_entry
- conversation_state
- label_scan
- daily_summary
- alembic_version

### Test Database Connection
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c "SELECT NOW();"
```

**Expected**: Current timestamp

---

## ✅ 7. Service Health Checks

### Agent API Health
```bash
curl http://localhost:8000/v1/health
```

**Expected**: `{"status":"healthy","service":"agent-api"}`

### Redis Connection
```bash
docker-compose exec redis redis-cli ping
```

**Expected**: `PONG`

### PostgreSQL Connection
```bash
docker-compose exec postgres pg_isready -U nutrition_user
```

**Expected**: `accepting connections`

---

## ✅ 8. Bot Connectivity

### Check Bot Info
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

**Expected**: JSON with bot info
```json
{
  "ok": true,
  "result": {
    "id": 1234567890,
    "is_bot": true,
    "first_name": "YourBotName",
    "username": "yourbotusername"
  }
}
```

### Check Webhook Status
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

**Expected**: `"url": ""` (empty, because we use polling)

### Find Bot in Telegram
- [ ] Open Telegram
- [ ] Search for bot username
- [ ] Bot appears in search results
- [ ] Can start chat with bot

---

## ✅ 9. First Message Test

### Send /start Command
1. Open chat with your bot in Telegram
2. Send: `/start`

**Expected response** (within 5 seconds):
```
👋 Привет, [YourName]!

Я помогу вам отслеживать питание с помощью ИИ.
...
```

### Check Bot Logs
```bash
docker-compose logs telegram-bot | tail -20
```

**Expected log entries**:
- "User [TELEGRAM_ID] started bot"
- "Received message from user"
- No ERROR lines

### Check API Logs
```bash
docker-compose logs agent-api | tail -20
```

**Expected log entries**:
- "Processing message from telegram_id"
- "Created new user" or "Found existing user"
- No ERROR lines

### Verify User in Database
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT id, telegram_id, first_name, created_at FROM user_profile ORDER BY created_at DESC LIMIT 1;"
```

**Expected**: Your user record

---

## ✅ 10. Simple Food Logging Test

### Send Simple Message
Send: `Съел 2 яйца`

**Expected**:
- Bot responds within 6 seconds
- May ask clarification: "Сколько грамм?"
- OR processes directly if weight is implied

### If Clarification Requested
Respond: `100г`

**Expected**:
- Bot searches FatSecret
- Finds eggs
- Saves entry
- Shows totals

### Final Response Format
```
✅ Сохранено!

📊 Итого за сегодня:
Калории: ~140 ккал
Белки: ~12г
Углеводы: ~1г
Жиры: ~10г
```

### Verify Entry in Database
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT food_name, calories, protein FROM food_log_entry ORDER BY created_at DESC LIMIT 1;"
```

**Expected**: Your egg entry with nutrition data

---

## ✅ 11. Report Test

### Request Daily Report
Send: `/today`

**Expected response**:
```
📊 **Отчёт за сегодня**

🔥 Калории: 140 ккал
🥩 Белки: 12г
...
📝 **Записей:** 1
```

### Request Weekly Report
Send: `/week`

**Expected response**:
```
📊 **Отчёт за неделю**

Калории за последние 7 дней:
...
```

---

## ✅ 12. Performance Check

### Response Times

Monitor with:
```bash
docker-compose logs -f agent-api telegram-bot
```

**Targets**:
- Bot receives message → API processes → Response: **< 6 seconds**
- Report generation: **< 2 seconds**
- Database queries: **< 500ms**

---

## 🚨 Troubleshooting

### If startup fails:
1. Check Docker is running
2. Verify .env file has all values
3. Check logs: `docker-compose logs`
4. Verify ports are free
5. Try clean restart:
   ```bash
   docker-compose down -v
   ./scripts/startup.sh
   ```

### If bot doesn't respond:
1. Check bot token is correct
2. Verify bot logs: `docker-compose logs telegram-bot`
3. Check API is reachable: `curl http://localhost:8000/v1/health`
4. Restart bot: `docker-compose restart telegram-bot`

### If migrations fail:
1. Check database is running: `docker-compose ps postgres`
2. Verify connection: `docker-compose exec postgres psql -U nutrition_user -l`
3. Reset database (⚠️ deletes all data):
   ```bash
   docker-compose down -v
   docker-compose up -d postgres redis
   sleep 10
   docker-compose up -d agent-api
   docker-compose exec agent-api alembic upgrade head
   docker-compose up -d telegram-bot
   ```

### If FatSecret search fails:
1. Verify credentials in .env
2. Test OAuth: See "FatSecret API Credentials" section above
3. Check MCP server logs: `docker-compose logs mcp-fatsecret`
4. Verify network: `docker-compose exec agent-api ping mcp-fatsecret`

---

## ✅ Final Checklist Summary

Before proceeding to production testing:

- [ ] All services start without errors
- [ ] Database migrations completed
- [ ] Bot responds to /start
- [ ] Bot can log a simple food item
- [ ] FatSecret search works
- [ ] Reports display correctly
- [ ] No critical errors in logs
- [ ] Performance meets targets
- [ ] User data persists after restart

---

## 📝 Notes

Keep track of:
- Your bot username: _______________
- Your telegram_id: _______________
- First test date: _______________
- Any issues encountered: _______________

---

## Next Steps

Once all checks pass:
1. ✅ Proceed to comprehensive testing (see TESTING.md)
2. Document any bugs or issues
3. Consider setting up monitoring (Prometheus, Grafana)
4. Plan production deployment
5. Set up backups for PostgreSQL

---

## Support

If you encounter issues:
1. Check this checklist first
2. Review TESTING.md for specific scenarios
3. Examine logs for error messages
4. Verify API credentials are valid
5. Check Docker resources are sufficient
