# Changelog

All notable changes to AiFood will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-07

### Added
- **CI/CD Pipeline**: GitHub Actions auto-deploy workflow
  - Automatic deployment on push to `main` branch
  - Smart change detection (plugin vs Docker services)
  - Conditional rebuild based on changed files
  - Health checks after deployment
  - Manual trigger with force rebuild option
  - Ignores documentation-only changes (`.md` files)

### Changed
- **Deployment Process**: From manual to automated
  - Push to `main` → automatic sync to production server
  - Plugin changes → rebuild + OpenClaw restart
  - Docker changes → container rebuild

### Infrastructure
- **GitHub Secrets**: VPS_HOST, VPS_USER, VPS_SSH_KEY configured
- **Workflow**: `.github/workflows/deploy.yml`

---

## [1.1.0] - 2026-03-04

### Added
- **New Tools**:
  - `delete_food_entry`: Delete food log entries by ID
  - `view_nutrition_profile`: View user profile with goals and daily progress
- **LLM Gateway Service** (port 9000):
  - Token optimization with sliding window (8 messages) and summarization (12k→1k tokens)
  - Response caching with Redis for deterministic queries
  - Quota tracking (100k tokens/day, $50/month limits)
  - Output profiles (brief: 512, standard: 1200, analysis: 4000 tokens)
  - Gemini 2.5 Flash integration via OpenAI-compatible API
- **Production Deployment**:
  - Deployed all services to production server (199.247.30.52)
  - Agent API service (FastAPI + LangGraph) on port 8000
  - OCR service (PaddleOCR) on port 8001
  - Full Docker Compose setup with health checks
- **Documentation**:
  - DEPLOYMENT_STATUS.md with live service monitoring
  - OPENCLAW_CONFIG.md with complete configuration guide
  - Updated QUICK_REFERENCE.md with all 7 tools

### Changed
- **AiFood Plugin**: Upgraded from 5 to 7 tools
- **Model Configuration**: Changed primary model from Ollama to Gemini 2.5 Flash
- **Server Architecture**: Consolidated all services on production server
- **Command Handler**: Fixed `/aifood` command response format (markdown → text)

### Fixed
- **Telegram Bot Conflict (Error 409)**: Resolved by deactivating services on gpu-server
- **API Key Security**: Fixed leaked API keys, implemented server-only storage
- **Kimi Adapter**: Removed incompatible Kimi adapter code
- **Model Availability**: Fixed gemini-2.0-flash-exp → gemini-2.5-flash (stable)
- **Vision API (2026-03-07)**: Fixed Agent API container using old leaked API key for Gemini Vision

### Removed
- Kimi adapter and aifood-kimi skill
- Ollama dependency (moved to separate GPU server)

### Deployment
- **Production Server**: 199.247.30.52 (aifood-prod)
  - LLM Gateway: ✅ Running (port 9000)
  - Agent API: ✅ Running (port 8000)
  - OCR Service: ✅ Running (port 8001)
  - Redis: ✅ Running (port 6379)
  - PostgreSQL: ✅ Running (port 5433)
  - OpenClaw Gateway: ✅ Running (port 18789)
  - Telegram Bot: @LenoxAI_bot ✅ Active
- **GPU Server**: 199.247.7.186 (deactivated for AiFood, Ollama only)

### Security
- API keys stored only on server (not in Git)
- New Gemini API key generated after leak detection
- Environment variables isolated from version control

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
