# AiFood - AI-Powered Nutrition Tracking

OpenClaw plugin для отслеживания питания с AI-ассистентом, FatSecret API и OCR распознаванием этикеток.

**Status**: ✅ **Production Ready** (OpenClaw Plugin Architecture)

## Features

### ✅ Implemented
- **Text Food Logging**: "Съел 2 яйца и 150г гречки" → автоматический поиск и логирование
- **FatSecret Integration**: Поиск продуктов из базы 1M+ items
- **Daily/Weekly Reports**: Отчёты с прогрессом по КБЖУ
- **Goal Tracking**: Установка и отслеживание целей по калориям и макросам
- **Nutrition Label OCR**: Распознавание русских этикеток (PaddleOCR + Gemini Vision fallback)
- **Multi-Platform**: Telegram, WhatsApp, Discord, Slack (через OpenClaw)

### 🚧 In Progress
- OCR Service deployment
- Label processing pipeline (LangGraph)
- Custom products database

## Tech Stack

**Frontend (Messaging)**
- OpenClaw Gateway (multi-platform messaging)
- Telegram Bot API
- WhatsApp (via OpenClaw)

**Backend (Plugin)**
- TypeScript/Node.js 18+
- OpenClaw Plugin SDK
- PostgreSQL 16 (nutrition data)
- FatSecret REST API

**AI/ML (Planned)**
- OCR Service: PaddleOCR (Russian)
- Vision API: Google Gemini 2.0 (fallback)
- Agent API: FastAPI + LangGraph

**Infrastructure**
- Server: Ubuntu 24.04 (CPU-only)
- Deployment: systemd services
- Database: PostgreSQL (port 5433)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         OpenClaw Gateway (Multi-Platform)                │
│  Telegram │ WhatsApp │ Discord │ Slack │ Signal         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              AiFood Plugin (TypeScript)                  │
│  ┌───────────────────────────────────────────────────┐ │
│  │                    Tools                           │ │
│  │  • log_food                                        │ │
│  │  • search_food                                     │ │
│  │  • daily_nutrition_report                         │ │
│  │  • weekly_nutrition_report                        │ │
│  │  • set_nutrition_goals                            │ │
│  │  • log_food_from_photo (planned)                  │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │                  Services                          │ │
│  │  • FatSecretClient (OAuth2)                       │ │
│  │  • DatabaseService (PostgreSQL)                   │ │
│  └───────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ PostgreSQL   │ │ FatSecret   │ │ Agent API    │
│ (port 5433)  │ │    API      │ │ (planned)    │
│              │ │             │ │              │
│ • food_log   │ │ OAuth 2.0   │ │ OCR + Vision │
│ • user_goals │ │ Search API  │ │ LangGraph    │
│ • profiles   │ │             │ │              │
└──────────────┘ └─────────────┘ └──────────────┘
```

## Installation

### Prerequisites

- **Node.js** 18+ and npm
- **PostgreSQL** 16+
- **OpenClaw** CLI installed
- **FatSecret API** credentials (Client ID + Secret)

### 1. Clone Repository

```bash
git clone <repository-url>
cd AiFood
```

### 2. Setup Database

```bash
# Create PostgreSQL database
createdb aifood

# Or using docker-compose (from _archive)
docker-compose up -d postgres
```

### 3. Install and Build Plugin

```bash
cd aifood-plugin

# Install dependencies
npm install

# Build plugin
npm run build

# Verify build
ls -la dist/
```

### 4. Configure Plugin

Create `~/.openclaw/openclaw.json` or update existing:

```json
{
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "fatsecretClientId": "YOUR_CLIENT_ID",
          "fatsecretClientSecret": "YOUR_SECRET",
          "databaseUrl": "postgresql://localhost:5433/aifood"
        }
      }
    }
  }
}
```

### 5. Install Plugin to OpenClaw

```bash
# Option A: Link for development (recommended)
openclaw plugins link ./aifood-plugin

# Option B: Install permanently
openclaw plugins install ./aifood-plugin
```

### 6. Restart OpenClaw Gateway

```bash
# If running as systemd service
sudo systemctl restart openclaw-gateway

# Or restart manually
openclaw gateway stop
openclaw gateway run
```

## Usage

### Via Telegram

1. Start conversation with your OpenClaw bot
2. Send: `/start`
3. Log food: "Съел 2 яйца на завтрак"
4. Check report: "Покажи отчёт за сегодня"
5. Set goals: "Установи цель: 2100 калорий, 230г белка"

### Available Commands

The AI automatically uses these tools based on your messages:

- **log_food**: Logs food with calories and macros
- **search_food**: Searches FatSecret database
- **daily_nutrition_report**: Shows daily summary
- **weekly_nutrition_report**: Shows 7-day summary
- **set_nutrition_goals**: Sets daily KBJU targets

### Example Conversations

```
User: Съел 200г куриной грудки и 150г гречки
Bot: ✅ Записано:
     • Куриная грудка, 200г: 220 ккал (Б: 46г, Ж: 2г, У: 0г)
     • Гречка вареная, 150г: 185 ккал (Б: 6г, Ж: 1г, У: 36г)

     Итого: 405 ккал

User: Покажи отчёт за сегодня
Bot: 📊 Отчёт за 1 марта 2026:

     🔥 Калории: 1,245 / 2,100 ккал (59%)
     🥩 Белок: 98 / 230г (43%)
     🍞 Углеводы: 120 / 144г (83%)
     🧈 Жиры: 35 / 89г (39%)
```

## Development

### Project Structure

```
aifood-plugin/
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── openclaw.plugin.json      # Plugin manifest
├── src/
│   ├── index.ts              # Entry point, tool registration
│   ├── types/index.ts        # TypeScript interfaces
│   ├── services/
│   │   ├── fatsecret.ts      # FatSecret API client
│   │   └── database.ts       # PostgreSQL service
│   └── tools/
│       ├── log-food.ts       # Food logging tool
│       ├── search-food.ts    # FatSecret search
│       ├── daily-report.ts   # Daily stats
│       ├── weekly-report.ts  # Weekly stats
│       └── set-goals.ts      # Goal setting
├── skills/
│   └── nutrition-advisor/
│       └── SKILL.md          # AI behavior instructions
└── dist/                     # Compiled output
```

### Development Workflow

```bash
cd aifood-plugin

# Watch mode (auto-rebuild on changes)
npm run watch

# Lint code
npm run lint

# Run tests
npm test

# Build for production
npm run build
```

### Database Schema

Main tables:

```sql
-- User profiles and settings
CREATE TABLE user_profile (
  telegram_id BIGINT PRIMARY KEY,
  username VARCHAR(255),
  first_name VARCHAR(255),
  target_calories INTEGER,
  target_protein INTEGER,
  target_carbs INTEGER,
  target_fat INTEGER
);

-- Food log entries
CREATE TABLE food_log_entry (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT REFERENCES user_profile(telegram_id),
  food_id VARCHAR(255),
  food_name VARCHAR(500) NOT NULL,
  calories NUMERIC(10, 2) NOT NULL,
  protein NUMERIC(10, 2),
  carbohydrates NUMERIC(10, 2),
  fat NUMERIC(10, 2),
  meal_type VARCHAR(20),
  consumed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User goals
CREATE TABLE user_goals (
  telegram_id BIGINT PRIMARY KEY,
  target_calories INTEGER,
  target_protein INTEGER,
  target_carbs INTEGER,
  target_fat INTEGER,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Deployment

### Server Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 22.04+

**Recommended (with OCR):**
- CPU: 4+ cores (or GPU)
- RAM: 16GB
- Storage: 50GB NVMe
- GPU: NVIDIA GTX 1060 6GB or better (for fast OCR)

### Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

Quick steps:

```bash
# 1. On server: Install dependencies
sudo apt update
sudo apt install -y nodejs npm postgresql-16

# 2. Setup PostgreSQL
sudo -u postgres createuser aifood
sudo -u postgres createdb aifood -O aifood

# 3. Clone and build
git clone <repo> /opt/aifood
cd /opt/aifood/aifood-plugin
npm install --production
npm run build

# 4. Install OpenClaw
curl -fsSL https://openclaw.com/install.sh | sh
openclaw configure

# 5. Install plugin
openclaw plugins install /opt/aifood/aifood-plugin

# 6. Setup systemd service
sudo cp deployment/openclaw-gateway.service /etc/systemd/system/
sudo systemctl enable openclaw-gateway
sudo systemctl start openclaw-gateway
```

### Environment Configuration

On server (`~/.openclaw/openclaw.json`):

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN",
      "dmPolicy": "open"
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.0-flash-exp"
      }
    }
  },
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "fatsecretClientId": "YOUR_CLIENT_ID",
          "fatsecretClientSecret": "YOUR_SECRET",
          "databaseUrl": "postgresql://aifood:password@localhost:5433/aifood"
        }
      }
    }
  }
}
```

## OCR Label Recognition (Planned)

Architecture for photo label processing:

```
User sends photo
     ↓
OpenClaw → log_food_from_photo tool
     ↓
Agent API (FastAPI + LangGraph)
     ↓
1. Download image
2. Preprocess (rotate, deskew, upscale)
3. OCR Service (PaddleOCR, Russian)
4. Quality check (confidence + markers)
5a. Parse OCR text (regex) OR
5b. Gemini Vision fallback
6. Validate nutrition data
7. Create custom product
8. Store scan metadata
     ↓
Confirmation dialog
     ↓
Log to food_log_entry
```

See [docs/LABEL_RECOGNITION.md](docs/LABEL_RECOGNITION.md) for details.

## Troubleshooting

### Plugin Not Loading

```bash
# Check OpenClaw logs
journalctl -u openclaw-gateway -f

# Verify plugin installation
openclaw plugins list

# Check plugin build
cd aifood-plugin && npm run build
```

### Database Connection Errors

```bash
# Test PostgreSQL connection
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT 1"

# Check running processes
sudo netstat -tlnp | grep 5433
```

### FatSecret API Errors

- Verify credentials in `~/.openclaw/openclaw.json`
- Check OAuth token expiration (auto-refreshes)
- Review logs: `journalctl -u openclaw-gateway | grep FatSecret`

## Performance

**Current (CPU-only server):**
- Text logging: ~2-5 seconds
- FatSecret search: ~1-2 seconds
- Daily report: ~1 second

**With GPU (planned):**
- OCR processing: ~3-5 seconds
- Vision fallback: ~5-10 seconds

## API Documentation

OpenClaw Plugin API:
- [Plugin SDK Docs](https://docs.openclaw.ai/plugins)
- [Tool Registration](https://docs.openclaw.ai/plugins/tools)

FatSecret API:
- [Platform API Docs](https://platform.fatsecret.com/api/)

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and test
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

## License

MIT License - see [LICENSE](LICENSE) file

## Support

- GitHub Issues: [link to issues]
- Documentation: [link to docs]
- Email: support@example.com

## Roadmap

- [x] OpenClaw plugin architecture
- [x] FatSecret integration
- [x] Basic food logging
- [x] Daily/weekly reports
- [x] Goal tracking
- [ ] OCR label recognition
- [ ] Custom products database
- [ ] Meal planning
- [ ] Recipe tracking
- [ ] Multi-language support
- [ ] Fitness tracker integration

## Credits

- **OpenClaw**: Multi-platform messaging framework
- **FatSecret**: Nutrition database API
- **PaddleOCR**: OCR engine (planned)
- **Google Gemini**: Vision AI (planned)

---

Built with ❤️ using OpenClaw Plugin SDK
