# Development Workflow

## Запуск проекта

### Quick Start
```bash
# 1. Настройка окружения
cp .env.example .env
# Заполнить: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, FATSECRET_*

# 2. Запуск всех сервисов
./scripts/startup.sh
```

### Manual Start
```bash
docker-compose up --build -d
docker-compose exec agent-api alembic upgrade head
docker-compose logs -f
```

### Остановка
```bash
./scripts/stop.sh
# или
docker-compose down
```

## Docker Commands

```bash
# Статус сервисов
docker-compose ps

# Логи
docker-compose logs -f                    # Все
docker-compose logs -f agent-api          # Только API
docker-compose logs -f telegram-bot       # Только бот

# Rebuild одного сервиса
docker-compose up -d --build agent-api

# Shell в контейнер
docker-compose exec agent-api bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot
```

## Database Migrations (Alembic)

```bash
# Применить все миграции
docker-compose exec agent-api alembic upgrade head

# Создать новую миграцию
docker-compose exec agent-api alembic revision --autogenerate -m "Add new_column to table"

# Откатить последнюю миграцию
docker-compose exec agent-api alembic downgrade -1

# Показать текущую версию
docker-compose exec agent-api alembic current

# История миграций
docker-compose exec agent-api alembic history
```

## Linting & Formatting

```bash
# Black — форматирование
docker-compose exec agent-api black src/

# isort — сортировка импортов
docker-compose exec agent-api isort src/

# Flake8 — линтинг
docker-compose exec agent-api flake8 src/

# mypy — проверка типов
docker-compose exec agent-api mypy src/

# Все вместе
docker-compose exec agent-api bash -c "black src/ && isort src/ && flake8 src/ && mypy src/"
```

## Configuration

Конфигурация через `pydantic_settings.BaseSettings`:

```python
# services/agent-api/src/config.py
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # LLM
    LLM_PROVIDER: str = "openai"  # "ollama" or "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_TEXT: str = "gpt-4-turbo-preview"
    OPENAI_MODEL_VISION: str = "gpt-4o"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()
```

### Основные переменные окружения

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `OPENAI_API_KEY` | OpenAI API key |
| `FATSECRET_CLIENT_ID` | FatSecret Client ID |
| `FATSECRET_CLIENT_SECRET` | FatSecret Client Secret |
| `LLM_PROVIDER` | "openai" или "ollama" |

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs

# Database check
docker-compose exec postgres pg_isready -U nutrition_user -d nutrition_bot
```

## Debugging

### Логи в реальном времени
```bash
docker-compose logs -f --tail=100 agent-api
```

### Python debugger в контейнере
```python
# В коде
import pdb; pdb.set_trace()

# Запуск с attach
docker-compose run --service-ports agent-api
```

### Database inspection
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot

# Полезные запросы
\dt                                    -- список таблиц
SELECT * FROM user_profile LIMIT 5;   -- пользователи
SELECT * FROM food_log_entry WHERE user_id = 1 ORDER BY consumed_at DESC LIMIT 10;
```

## Git Workflow

```bash
# Перед коммитом
docker-compose exec agent-api bash -c "black src/ && isort src/ && flake8 src/"

# Проверка типов
docker-compose exec agent-api mypy src/

# Тесты
docker-compose exec agent-api pytest
```

## Production Deploy

### Автодеплой
Push в `main` ветку автоматически запускает деплой через GitHub Actions.

```bash
git add .
git commit -m "feat: description"
git push origin main
# → Автоматический деплой на сервер
```

### Ручной деплой на сервере
```bash
cd /opt/aifood
./scripts/deploy.sh
```

### Production команды
```bash
# На сервере
cd /opt/aifood

# Логи production
docker-compose -f docker-compose.prod.yml logs -f

# Статус
docker-compose -f docker-compose.prod.yml ps

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Миграции
docker-compose -f docker-compose.prod.yml exec agent-api alembic upgrade head
```

### Бэкап БД
```bash
# Создать
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U nutrition_user nutrition_bot > backup_$(date +%Y%m%d).sql
```
