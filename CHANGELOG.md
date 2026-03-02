# Changelog

All notable changes to AiFood will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-02

### Added
- **OpenClaw Plugin Architecture**: Migrated from standalone Telegram bot to OpenClaw plugin
- **Multi-Platform Support**: Works on Telegram, WhatsApp, Discord, Slack via OpenClaw
- **FatSecret Integration**: Full OAuth2 integration with FatSecret Platform API
- **Core Tools**:
  - `log_food`: Log food entries with automatic FatSecret search
  - `search_food`: Search FatSecret database (1M+ food items)
  - `daily_nutrition_report`: Daily KBJU summary with progress
  - `weekly_nutrition_report`: 7-day nutrition trends
  - `set_nutrition_goals`: Set and track daily targets
- **Database Schema**: PostgreSQL tables for users, goals, food logs
- **Skill System**: AI behavior defined in `SKILL.md` for nutrition advisor
- **Documentation**:
  - Comprehensive README with installation guide
  - Deployment guide for production servers
  - OpenClaw setup guide with model selection
  - Plugin development documentation
- **Deployment Files**:
  - Systemd service configuration
  - Example OpenClaw configs
  - Database migration scripts

### Changed
- **Architecture**: Moved from FastAPI+aiogram to OpenClaw plugin
- **Language**: Backend changed from Python to TypeScript/Node.js
- **Deployment**: Simplified deployment with systemd instead of Docker
- **AI Models**: Support for Gemini, Groq, Ollama (previously OpenAI only)

### Removed
- Legacy Python services (moved to `_archive/`):
  - `services/telegram-bot/` (aiogram)
  - `services/agent-api/` (FastAPI + LangGraph)
  - `services/mcp-fatsecret/` (MCP server)
- Docker Compose deployment (kept in archive for reference)

## [0.2.0] - 2026-02-28 (Archived)

### Added
- Photo label recognition with GPT-4o Vision
- Custom products from nutrition labels
- OCR preprocessing pipeline
- Confirmation workflow for label data

### Changed
- Upgraded to aiogram 3.x
- Added LangGraph for state management
- Improved error handling

## [0.1.0] - 2026-02-20 (Archived)

### Added
- Initial MVP release
- Telegram bot with basic food logging
- FatSecret API integration via MCP
- PostgreSQL database
- Daily/weekly reports
- AI recommendations

---

## Migration Guide: 0.2.x → 1.0.0

If you're migrating from the old Python/Docker setup:

### Data Migration

1. Export existing data:
```bash
# From old setup
docker-compose exec postgres pg_dump -U nutrition_user nutrition_bot > backup.sql
```

2. Import to new setup:
```bash
# On new server
psql -h localhost -p 5433 -U aifood -d aifood < backup.sql
```

### Configuration Migration

Old `.env` variables → New `openclaw.json`:

| Old (.env) | New (openclaw.json) |
|------------|---------------------|
| `TELEGRAM_BOT_TOKEN` | `channels.telegram.botToken` |
| `OPENAI_API_KEY` | `~/.openclaw/agents/main/agent/auth.json` |
| `FATSECRET_CLIENT_ID` | `plugins.entries.aifood.config.fatsecretClientId` |
| `FATSECRET_CLIENT_SECRET` | `plugins.entries.aifood.config.fatsecretClientSecret` |
| `DATABASE_URL` | `plugins.entries.aifood.config.databaseUrl` |

### Breaking Changes

- **No Docker**: New setup runs directly with systemd
- **No FastAPI endpoints**: Functionality moved to OpenClaw plugin tools
- **No Python**: Plugin is TypeScript/Node.js
- **Different database schema**: May need migrations

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for full setup instructions.
