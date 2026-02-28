# Quick Start Guide - AI Nutrition Bot

Get up and running in 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- API credentials ready:
  - Telegram Bot Token (from @BotFather)
  - OpenAI API Key (with GPT-4 access)
  - FatSecret Client ID & Secret

## 1. Configure Environment (2 min)

```bash
cd /Users/sandro/Documents/Other/AiFood

# Edit .env file with your credentials
nano .env
# or
open .env
```

Replace these placeholders:
```bash
TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE
OPENAI_API_KEY=YOUR_ACTUAL_KEY_HERE
FATSECRET_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID_HERE
FATSECRET_CLIENT_SECRET=YOUR_ACTUAL_SECRET_HERE
```

Save and close.

## 2. Start Services (2 min)

```bash
# One command to start everything
./scripts/startup.sh
```

Wait for:
- ✅ PostgreSQL ready
- ✅ Redis ready
- ✅ Migrations completed
- ✅ All services up

## 3. Test Bot (1 min)

1. Open Telegram
2. Search for your bot
3. Send: `/start`
4. Send: `Съел 2 яйца 100г`
5. Send: `/today`

**Expected**: Bot responds to all commands within 6 seconds.

## Done! 🎉

Your bot is now running and ready to track nutrition.

---

## Quick Commands

### Start/Stop
```bash
./scripts/startup.sh   # Start all services
./scripts/stop.sh      # Stop all services
```

### View Logs
```bash
docker-compose logs -f                # All services
docker-compose logs -f telegram-bot   # Bot only
docker-compose logs -f agent-api      # API only
```

### Check Status
```bash
docker-compose ps                      # Service status
curl http://localhost:8000/v1/health  # API health
```

### Database
```bash
# View users
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT * FROM user_profile;"

# View food entries
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT food_name, calories FROM food_log_entry ORDER BY created_at DESC LIMIT 10;"
```

---

## Bot Commands

- `/start` - Register and see welcome
- `/today` - View daily nutrition report
- `/week` - View weekly report
- `/help` - Show help message

### Food Logging Examples

```
Съел 2 яйца 100г
Съел 150г гречки варёной
200g chicken breast
Протеиновый батончик 50г
Ate 2 eggs and 100g rice
```

---

## Troubleshooting

### Bot not responding?
```bash
# Check logs
docker-compose logs telegram-bot | tail -50

# Restart bot
docker-compose restart telegram-bot
```

### Can't connect to database?
```bash
# Check database is up
docker-compose ps postgres

# Restart all services
./scripts/stop.sh
./scripts/startup.sh
```

### "User not found" error?
```bash
# Send /start to register first
# Or check database:
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT telegram_id FROM user_profile;"
```

---

## Next Steps

- **Testing**: See [TESTING.md](TESTING.md) for comprehensive test scenarios
- **Detailed Setup**: See [PRE_FLIGHT_CHECKLIST.md](PRE_FLIGHT_CHECKLIST.md)
- **Architecture**: See [README.md](README.md)

---

## Architecture Overview

```
Telegram Users
     ↓
[telegram-bot] - Receives messages
     ↓ HTTP
[agent-api] - LangGraph processes input
     ↓ MCP
[mcp-fatsecret] - Searches nutrition data
     ↓
[PostgreSQL] - Stores user data & food logs
[Redis] - Caches conversation state
```

---

## Project Structure

```
AiFood/
├── scripts/
│   ├── startup.sh       ← Start everything
│   └── stop.sh          ← Stop everything
├── services/
│   ├── telegram-bot/    ← Bot handlers
│   ├── agent-api/       ← FastAPI + LangGraph
│   └── mcp-fatsecret/   ← FatSecret integration
├── .env                 ← YOUR CREDENTIALS HERE
├── docker-compose.yml   ← Service orchestration
├── README.md            ← Full documentation
├── TESTING.md           ← Test scenarios
└── PRE_FLIGHT_CHECKLIST.md  ← Detailed setup

Total: 65 Python files, ~6,500 lines of code
```

---

## Key Features

✅ **Text Input**: Natural language food logging
✅ **Smart Clarifications**: Asks for missing info (weight, cooking method)
✅ **FatSecret Search**: Real nutrition data from 500k+ foods
✅ **Inline Keyboards**: Easy selection with buttons
✅ **Daily/Weekly Reports**: Track nutrition progress
✅ **AI Advice**: Personalized recommendations
✅ **Multi-language**: Russian and English support

---

## Performance

- Text input → Response: **< 6 seconds**
- Report generation: **< 2 seconds**
- Database queries: **< 500ms**

---

## Support

Issues? Check in this order:

1. ✅ Docker is running
2. ✅ All credentials in .env are correct
3. ✅ All services are up: `docker-compose ps`
4. ✅ No errors in logs: `docker-compose logs | grep ERROR`
5. ✅ API is healthy: `curl http://localhost:8000/v1/health`

Still stuck? Review:
- [PRE_FLIGHT_CHECKLIST.md](PRE_FLIGHT_CHECKLIST.md) - Detailed setup
- [TESTING.md](TESTING.md) - Common issues & solutions
- Service logs: `docker-compose logs [service-name]`

---

## Production Checklist

Before deploying to production:

- [ ] Change default database password in .env
- [ ] Set ENVIRONMENT=production
- [ ] Setup proper logging (structured logs)
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Setup database backups
- [ ] Use secrets management (not .env file)
- [ ] Setup SSL/TLS for API endpoints
- [ ] Configure rate limiting
- [ ] Setup alerting for errors
- [ ] Document incident response procedures

---

## License & Credits

Built with:
- aiogram 3 - Telegram Bot Framework
- FastAPI - Web Framework
- LangGraph - AI Workflow Orchestration
- OpenAI GPT-4 - Text Parsing & Vision
- FatSecret API - Nutrition Database
- PostgreSQL - Database
- Redis - Cache & State Management
