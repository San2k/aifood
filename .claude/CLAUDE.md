# AiFood — AI Nutrition Tracking Bot

Telegram-бот для отслеживания питания с использованием GPT-4 и FatSecret API.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, LangGraph
- **Bot**: aiogram 3
- **Database**: PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic
- **Cache**: Redis 7
- **AI**: OpenAI GPT-4-turbo (text), GPT-4o (vision)
- **Food Data**: FatSecret API via MCP
- **Container**: Docker Compose

## Quick Commands

### Запуск
```bash
./scripts/startup.sh          # Полный запуск (рекомендуется)
docker-compose up --build -d  # Manual
```

### Остановка
```bash
./scripts/stop.sh
docker-compose down
```

### Логи
```bash
docker-compose logs -f agent-api
docker-compose logs -f telegram-bot
```

### Миграции БД
```bash
docker-compose exec agent-api alembic upgrade head
docker-compose exec agent-api alembic revision --autogenerate -m "Description"
```

### Тестирование
```bash
docker-compose exec agent-api pytest
docker-compose exec agent-api pytest --cov=src --cov-report=html
docker-compose exec agent-api pytest -v tests/test_api/
```

### Линтинг
```bash
docker-compose exec agent-api black src/
docker-compose exec agent-api isort src/
docker-compose exec agent-api flake8 src/
docker-compose exec agent-api mypy src/
```

## Структура проекта

```
services/
├── agent-api/           # FastAPI + LangGraph backend
│   ├── src/
│   │   ├── api/v1/      # REST endpoints
│   │   ├── graph/       # LangGraph state machine
│   │   ├── db/          # SQLAlchemy models & repos
│   │   └── services/    # LLM, MCP, Redis
│   └── migrations/      # Alembic
├── telegram-bot/        # aiogram 3
│   └── src/bot/
│       ├── handlers/    # Message handlers
│       └── keyboards/   # Inline keyboards
└── mcp-fatsecret/       # MCP server for FatSecret
```

## Ключевые файлы

| Файл | Назначение |
|------|------------|
| `services/agent-api/src/graph/graph.py` | LangGraph state machine |
| `services/agent-api/src/api/v1/endpoints/ingest.py` | Main API endpoint |
| `services/agent-api/src/config.py` | Configuration |
| `services/telegram-bot/src/bot/handlers/` | Telegram handlers |

## Правила

@import rules/safety.md
@import rules/code-style.md
@import rules/testing.md
@import rules/architecture.md
@import rules/dev-workflow.md
