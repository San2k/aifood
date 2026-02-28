# AI Nutrition Bot

Telegram-бот для отслеживания питания с ИИ-помощником на базе GPT-4, FatSecret API и LangGraph.

**Status**: ✅ **MVP Complete and Ready for Testing**

## 📚 Documentation

- **[Quick Start](QUICK_START.md)** - Get running in 5 minutes
- **[Pre-Flight Checklist](PRE_FLIGHT_CHECKLIST.md)** - Pre-launch verification
- **[Testing Guide](TESTING.md)** - Comprehensive test scenarios
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - What was built

## Features

### Phase 1 (MVP)
- ✅ Текстовый ввод еды ("Съел 2 яйца и 100г риса")
- ✅ Парсинг через GPT-4 с обязательными уточнениями
- ✅ Поиск продуктов в FatSecret API через MCP
- ✅ Логирование в дневник питания
- ✅ Отчёты /today и /week
- ✅ AI-рекомендации без галлюцинаций

### Phase 2
- ✅ Распознавание фото этикеток через GPT-4o Vision
- ✅ Подтверждение и коррекция OCR данных
- ✅ Создание кастомных продуктов из этикеток

## Tech Stack

- **Backend**: Python 3.11, FastAPI, LangGraph
- **Bot**: aiogram 3
- **AI**: OpenAI API (GPT-4.1, GPT-4o Vision)
- **Data**: FatSecret API через MCP
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Infrastructure**: Docker, Docker Compose

## Architecture

```
Telegram Users
     ↓
[telegram-bot] (aiogram 3)
     ↓ HTTP REST
[agent-api] (FastAPI + LangGraph)
     ↓ MCP stdio          ↓ HTTPS
[mcp-fatsecret]    [OpenAI API]
     ↓
[FatSecret API]

State: [Redis]
Data: [PostgreSQL]
```

## Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (от @BotFather)
- OpenAI API Key
- FatSecret API Credentials (Client ID + Secret)

## Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd AiFood

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
# - FATSECRET_CLIENT_ID
# - FATSECRET_CLIENT_SECRET
```

### 2. Start Services

**Option A: Use startup script (recommended)**

```bash
# Run startup script (builds, starts services, runs migrations)
./scripts/startup.sh

# Stop all services
./scripts/stop.sh
```

**Option B: Manual startup**

```bash
# Build and start all services
docker-compose up -d

# Wait for databases to be ready
sleep 10

# Run database migrations
docker-compose exec agent-api alembic upgrade head

# Check services status
docker-compose ps

# View logs
docker-compose logs -f telegram-bot
docker-compose logs -f agent-api
```

### 3. Verify Database

```bash
# Verify database tables
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c "\dt"

# Check user_profile table
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c "SELECT * FROM user_profile LIMIT 5;"
```

### 4. Test Bot

Open Telegram and find your bot. Send:
- `/start` - Register
- "Съел 2 яйца" - Log food
- `/today` - View daily summary
- Send photo of nutrition label - OCR test

## Project Structure

```
AiFood/
├── docker-compose.yml          # Services orchestration
├── .env                        # Environment configuration
├── services/
│   ├── telegram-bot/           # Telegram bot (aiogram 3)
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── bot/handlers/   # Message handlers
│   │   │   └── services/       # Agent API client
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── agent-api/              # FastAPI + LangGraph
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/v1/         # REST API endpoints
│   │   │   ├── graph/          # LangGraph state machine
│   │   │   ├── services/       # OpenAI, MCP, Redis
│   │   │   └── db/             # Database models
│   │   ├── migrations/         # Alembic migrations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── mcp-fatsecret/          # MCP Server for FatSecret
│       ├── src/
│       │   ├── main.py
│       │   ├── server/tools/   # MCP tools
│       │   └── client/         # FatSecret API client
│       ├── Dockerfile
│       └── requirements.txt
└── scripts/                    # Utility scripts
```

## Development

### Running Tests

```bash
# Run all tests
docker-compose exec agent-api pytest

# Run specific test file
docker-compose exec agent-api pytest tests/test_graph/test_nodes.py

# Run with coverage
docker-compose exec agent-api pytest --cov=src --cov-report=html
```

### Database Migrations

```bash
# Create new migration
docker-compose exec agent-api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec agent-api alembic upgrade head

# Rollback migration
docker-compose exec agent-api alembic downgrade -1
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f telegram-bot
docker-compose logs -f agent-api

# Last 100 lines
docker-compose logs --tail=100 agent-api
```

### Rebuild Services

```bash
# Rebuild specific service
docker-compose build agent-api

# Rebuild all services
docker-compose build

# Rebuild and restart
docker-compose up -d --build
```

## API Documentation

Once services are running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Bot Commands

- `/start` - Регистрация и приветствие
- `/profile` - Настройки профиля (цели, макросы)
- `/today` - Отчёт за сегодня
- `/week` - Отчёт за неделю
- `/advice` - Получить рекомендации
- `/help` - Справка

## Usage Examples

### Text Input
```
User: Съел 2 яйца и 150г гречки
Bot: Гречка сухая или варёная?
User: Варёная
Bot: ✅ Добавлено:
     • 2 яйца (140 ккал)
     • 150г гречки вареной (195 ккал)
     Итого: 335 ккал
```

### Photo Label
```
User: [uploads nutrition label photo]
Bot: 📸 Распознал этикетку:
     Protein Bar
     На 100г: 350 ккал, Б: 20г, Ж: 10г, У: 40г
     [✅ Верно] [✏️ Исправить]
User: [clicks ✅ Верно]
Bot: ✅ Добавлено: Protein Bar (350 ккал)
```

## Environment Variables

Key variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrition_bot

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_TEXT=gpt-4-turbo-preview
OPENAI_MODEL_VISION=gpt-4o

# FatSecret
FATSECRET_CLIENT_ID=...
FATSECRET_CLIENT_SECRET=...
```

## Troubleshooting

### Bot Not Responding
```bash
# Check bot logs
docker-compose logs telegram-bot

# Restart bot
docker-compose restart telegram-bot
```

### Database Connection Issues
```bash
# Check postgres status
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready -U nutrition_user
```

### Redis Connection Issues
```bash
# Check redis status
docker-compose exec redis redis-cli ping
```

### OpenAI API Errors
- Verify API key in `.env`
- Check quota: https://platform.openai.com/usage
- Review logs: `docker-compose logs agent-api`

## Performance Targets

- Text input → response: **< 6s** (p95)
- Photo input → OCR: **< 15s** (p95)
- /today report: **< 2s** (p95)

## Security Notes

- Never commit `.env` file
- Rotate API keys regularly
- Use strong database passwords
- Enable HTTPS in production
- Implement rate limiting

## Contributing

1. Create feature branch
2. Make changes
3. Run tests: `docker-compose exec agent-api pytest`
4. Submit pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]
- Email: [your-email]

## Roadmap

- [x] Phase 1: Text input + FatSecret
- [x] Phase 2: Photo labels + Vision AI
- [ ] Phase 3: Custom foods/recipes
- [ ] Phase 4: Production deployment + monitoring
- [ ] Meal planning feature
- [ ] Integration with fitness trackers
- [ ] Multi-language support
