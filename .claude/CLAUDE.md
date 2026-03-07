# AiFood — OpenClaw Nutrition Plugin

**Version**: 1.1.0 | **Status**: Production

OpenClaw плагин для отслеживания питания с AI-ассистентом, FatSecret API и OCR распознаванием этикеток.

## Tech Stack

- **Runtime**: Node.js 18+, TypeScript
- **AI Model**: Google Gemini 2.5 Flash
- **Database**: PostgreSQL 16
- **Food Data**: FatSecret API
- **OCR**: PaddleOCR + Gemini Vision (fallback)
- **Platform**: OpenClaw Gateway
- **Caching**: Redis

## Production Server

**Server**: 199.247.30.52 (aifood-prod)
**SSH**: `ssh aifood-prod`

| Service | Port | Container |
|---------|------|-----------|
| OpenClaw Gateway | 18789 | systemd |
| LLM Gateway | 9000 | aifood-llm-gateway |
| Agent API | 8000 | aifood-agent-api |
| OCR Service | 8001 | aifood-ocr-service |
| PostgreSQL | 5433 | aifood-postgres |
| Redis | 6379 | aifood-redis |

## Quick Commands

### Локальная разработка
```bash
cd aifood-plugin
npm install
npm run build
npm run watch        # TypeScript watch mode
```

### Деплой на сервер
```bash
# Обновить код
ssh aifood-prod "cd /opt/aifood && git pull origin main"

# Пересобрать плагин
ssh aifood-prod "cd /opt/aifood/aifood-plugin && npm install && npm run build"

# Переустановить плагин
ssh aifood-prod "rm -rf /root/.openclaw/extensions/aifood && openclaw plugins install /opt/aifood/aifood-plugin"

# Перезапустить OpenClaw
ssh aifood-prod "systemctl restart openclaw-gateway"

# Перезапустить Docker сервисы
ssh aifood-prod "cd /opt/aifood && docker compose --env-file .env up -d"
```

### Версионность
```bash
./scripts/bump-version.sh patch   # 1.1.0 → 1.1.1
./scripts/bump-version.sh minor   # 1.1.0 → 1.2.0
./scripts/bump-version.sh major   # 1.1.0 → 2.0.0
```

### Мониторинг
```bash
# Логи OpenClaw
ssh aifood-prod "journalctl -u openclaw-gateway -f"

# Логи Docker
ssh aifood-prod "docker logs -f aifood-agent-api"

# Health checks
ssh aifood-prod "curl -s localhost:9000/health && curl -s localhost:8000/health"
```

## Структура проекта

```
aifood/
├── VERSION                       # Текущая версия (1.1.0)
├── CHANGELOG.md                  # История изменений
├── VERSIONING.md                 # Гид по версионности
├── DEPLOYMENT_STATUS.md          # Статус production
│
├── aifood-plugin/                # OpenClaw плагин
│   ├── src/index.ts              # Entry point (7 tools)
│   ├── src/services/
│   │   ├── database.ts           # PostgreSQL
│   │   └── fatsecret.ts          # FatSecret API
│   └── package.json              # v1.1.0
│
├── services/
│   ├── llm-gateway/              # Gemini proxy + token optimization
│   │   ├── src/                  # TypeScript source
│   │   └── Dockerfile
│   ├── agent-api/                # FastAPI + LangGraph
│   │   ├── src/                  # Python source
│   │   └── Dockerfile
│   └── ocr-service/              # PaddleOCR
│       └── Dockerfile
│
├── scripts/
│   └── bump-version.sh           # Автоматизация версий
│
├── docker-compose.yml            # Production services
└── .claude/                      # Claude Code config
```

## OpenClaw Tools (7)

| Tool | Описание |
|------|----------|
| `log_food_entry` | Логирование еды с данными из FatSecret |
| `search_food` | Поиск калорийности и нутриентов |
| `get_daily_nutrition_report` | Отчёт за день |
| `get_weekly_nutrition_report` | Отчёт за неделю |
| `set_nutrition_goals` | Установка целей КБЖУ |
| `delete_food_entry` | Удаление записи из журнала |
| `view_nutrition_profile` | Просмотр профиля и прогресса |

**Команда**: `/aifood` — справка по командам

## Ключевые файлы

| Файл | Назначение |
|------|------------|
| `aifood-plugin/src/index.ts` | Entry point, регистрация 7 tools |
| `services/llm-gateway/src/index.ts` | LLM Gateway сервер |
| `services/agent-api/src/main.py` | Agent API FastAPI |
| `docker-compose.yml` | Production Docker config |
| `VERSION` | Текущая версия проекта |

## Конфигурация Production

### OpenClaw (`/root/.openclaw/openclaw.json`)
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.5-flash"
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

### Auth Profiles (`/root/.openclaw/agents/main/agent/auth-profiles.json`)
```json
{
  "profiles": {
    "google:default": {
      "type": "api_key",
      "provider": "google",
      "key": "<GEMINI_API_KEY>"
    }
  }
}
```

### Environment (`/opt/aifood/.env`)
```bash
POSTGRES_PASSWORD=<password>
GEMINI_API_KEY=<key>
GEMINI_MODEL=gemini-2.5-flash
```

## API Keys

**ВАЖНО**: API ключи хранятся ТОЛЬКО на сервере!

- `.env` файл НЕ в Git
- `auth-profiles.json` НЕ в Git
- В документации используй `<PLACEHOLDER>`

При смене ключа обновить:
1. `/opt/aifood/.env` (для Docker)
2. `/root/.openclaw/agents/main/agent/auth-profiles.json` (для OpenClaw)
3. Перезапустить: `docker compose --env-file .env up -d && systemctl restart openclaw-gateway`

## Архив

Старые Python сервисы в `_archive/`:
- FastAPI Telegram bot
- MCP FatSecret server
- Legacy Docker configs

## Документация

- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) — Production статус
- [VERSIONING.md](../VERSIONING.md) — Гид по версиям
- [CHANGELOG.md](../CHANGELOG.md) — История изменений
- [services/llm-gateway/README.md](../services/llm-gateway/README.md) — LLM Gateway API

## Правила

@import rules/safety.md
@import rules/code-style.md
@import rules/testing.md
@import rules/architecture.md
@import rules/dev-workflow.md
