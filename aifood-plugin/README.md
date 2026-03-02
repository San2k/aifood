# AiFood Plugin for OpenClaw

OpenClaw plugin for AI-powered nutrition tracking with FatSecret API integration.

## Features

- 🍎 **Food Logging**: Log meals with automatic nutritional data lookup
- 🔍 **FatSecret Search**: Access 1M+ food items database
- 📊 **Daily Reports**: KBJU tracking and progress monitoring
- 📈 **Weekly Trends**: 7-day nutrition analysis
- 🎯 **Goal Setting**: Set and track daily nutrition targets
- 🌍 **Multi-Platform**: Works on Telegram, WhatsApp, Discord, Slack

## Installation

### Prerequisites

- OpenClaw CLI installed
- Node.js 18+
- PostgreSQL 16+
- FatSecret API credentials

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd AiFood/aifood-plugin

# 2. Install dependencies
npm install

# 3. Build plugin
npm run build

# 4. Install to OpenClaw
openclaw plugins install .

# 5. Configure (see Configuration section)

# 6. Restart OpenClaw
openclaw gateway restart
```

## Configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "aifood": {
        "enabled": true,
        "config": {
          "fatsecretClientId": "YOUR_FATSECRET_CLIENT_ID",
          "fatsecretClientSecret": "YOUR_FATSECRET_CLIENT_SECRET",
          "databaseUrl": "postgresql://aifood:password@localhost:5433/aifood"
        }
      }
    }
  }
}
```

Get FatSecret credentials: https://platform.fatsecret.com/api/

## Tools

The plugin registers the following tools for AI use:

### `log_food`

Logs food entry with nutritional data.

**Parameters:**
- `foodName` (string, required): Food item name
- `calories` (number, required): Calories per serving
- `servingSize` (number, required): Serving size in grams
- `protein` (number, optional): Protein in grams
- `carbs` (number, optional): Carbohydrates in grams
- `fat` (number, optional): Fat in grams
- `fiber` (number, optional): Fiber in grams
- `meal` (string, optional): breakfast, lunch, dinner, snack
- `date` (string, optional): Date in YYYY-MM-DD format

**Example:**
```typescript
{
  "foodName": "Куриная грудка",
  "calories": 220,
  "servingSize": 200,
  "protein": 46,
  "carbs": 0,
  "fat": 2,
  "meal": "lunch"
}
```

### `search_food`

Searches FatSecret database for food items.

**Parameters:**
- `query` (string, required): Search query
- `maxResults` (number, optional): Max results to return (default: 5)

**Returns:** Array of food items with nutritional data.

### `daily_nutrition_report`

Generates daily nutrition summary.

**Parameters:**
- `date` (string, optional): Date in YYYY-MM-DD (defaults to today)

**Returns:** Daily totals, goal progress, meal breakdown.

### `weekly_nutrition_report`

Generates 7-day nutrition trends.

**Parameters:**
- `endDate` (string, optional): End date (defaults to today)

**Returns:** Weekly averages, trends, goal adherence.

### `set_nutrition_goals`

Sets daily nutrition targets.

**Parameters:**
- `calories` (number, required): Daily calorie target
- `protein` (number, optional): Protein target in grams
- `carbs` (number, optional): Carbs target in grams
- `fat` (number, optional): Fat target in grams
- `fiber` (number, optional): Fiber target in grams

## Development

### Project Structure

```
aifood-plugin/
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── openclaw.plugin.json      # Plugin manifest
├── src/
│   ├── index.ts              # Entry point
│   ├── types/
│   │   └── index.ts          # Type definitions
│   ├── services/
│   │   ├── fatsecret.ts      # FatSecret API client
│   │   └── database.ts       # PostgreSQL service
│   └── tools/
│       ├── log-food.ts       # Food logging
│       ├── search-food.ts    # FatSecret search
│       ├── daily-report.ts   # Daily stats
│       ├── weekly-report.ts  # Weekly stats
│       └── set-goals.ts      # Goal management
├── skills/
│   └── nutrition-advisor/
│       └── SKILL.md          # AI behavior
└── dist/                     # Compiled output
```

### Build Commands

```bash
# Install dependencies
npm install

# Development (watch mode)
npm run watch

# Build for production
npm run build

# Lint code
npm run lint

# Run tests
npm test
```

### Adding New Tools

1. Create tool file in `src/tools/`:

```typescript
// src/tools/my-tool.ts
import type { Tool } from '../types';

export function createMyTool(): Tool {
  return {
    name: 'my_tool',
    description: 'What this tool does',
    parameters: {
      type: 'object',
      properties: {
        param1: { type: 'string', description: 'Param description' },
      },
      required: ['param1'],
    },
    handler: async (params, context) => {
      // Implementation
      return {
        success: true,
        data: result,
      };
    },
  };
}
```

2. Register in `src/index.ts`:

```typescript
import { createMyTool } from './tools/my-tool';

export async function register(api: PluginAPI) {
  api.registerTool(createMyTool());
}
```

3. Rebuild and test:

```bash
npm run build
openclaw plugins reload aifood
```

## Database Schema

The plugin uses these PostgreSQL tables:

```sql
-- User profiles
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
  consumed_at TIMESTAMPTZ NOT NULL
);

-- User goals
CREATE TABLE user_goals (
  telegram_id BIGINT PRIMARY KEY,
  target_calories INTEGER,
  target_protein INTEGER,
  target_carbs INTEGER,
  target_fat INTEGER
);
```

## Troubleshooting

### Plugin Not Loading

```bash
# Check plugin status
openclaw plugins list

# View logs
journalctl -u openclaw-gateway | grep -i aifood

# Rebuild plugin
npm run build

# Reinstall
openclaw plugins uninstall aifood
openclaw plugins install .
```

### Database Connection Failed

```bash
# Test connection
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT 1;"

# Check config
cat ~/.openclaw/openclaw.json | grep databaseUrl
```

### FatSecret API Errors

- Verify credentials in `openclaw.json`
- Check API quotas at https://platform.fatsecret.com
- Review logs for OAuth errors

## API Documentation

- **OpenClaw Plugin SDK**: https://docs.openclaw.ai/plugins
- **FatSecret Platform API**: https://platform.fatsecret.com/api/

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests: `npm test`
5. Submit pull request

## License

MIT License - see [LICENSE](../LICENSE) file

## Support

- GitHub Issues: [link]
- Documentation: [link]
- Email: support@example.com
