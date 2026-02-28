# AiFood — OpenClaw Nutrition Plugin

OpenClaw плагин для отслеживания питания с использованием FatSecret API.

## Tech Stack

- **Runtime**: Node.js 18+, TypeScript
- **Database**: PostgreSQL
- **Food Data**: FatSecret API
- **Platform**: OpenClaw (local AI assistant)

## Quick Commands

### Сборка плагина
```bash
cd aifood-plugin
npm install
npm run build
```

### Установка в OpenClaw
```bash
openclaw plugins install ./aifood-plugin
```

### Разработка
```bash
cd aifood-plugin
npm run watch        # TypeScript watch mode
npm run lint         # ESLint
npm test             # Jest тесты
```

### База данных
```bash
# PostgreSQL должен быть запущен
psql -d aifood -c "\dt"
```

## Структура проекта

```
aifood-plugin/
├── openclaw.plugin.json      # Манифест плагина
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # Entry point
│   ├── types/index.ts        # TypeScript типы
│   ├── services/
│   │   ├── fatsecret.ts      # FatSecret API клиент
│   │   └── database.ts       # PostgreSQL сервис
│   └── tools/
│       ├── log-food.ts       # Логирование еды
│       ├── search-food.ts    # Поиск в FatSecret
│       ├── daily-report.ts   # Дневной отчёт
│       ├── weekly-report.ts  # Недельный отчёт
│       └── set-goals.ts      # Установка целей
└── skills/
    └── nutrition-advisor/
        └── SKILL.md          # AI-советник по питанию
```

## OpenClaw Tools

| Tool | Описание |
|------|----------|
| `log_food` | Логирование еды с данными из FatSecret |
| `search_food` | Поиск калорийности и нутриентов |
| `daily_nutrition_report` | Отчёт за день |
| `weekly_nutrition_report` | Отчёт за неделю |
| `set_nutrition_goals` | Установка целей КБЖУ |

## Ключевые файлы

| Файл | Назначение |
|------|------------|
| `aifood-plugin/src/index.ts` | Entry point, регистрация tools |
| `aifood-plugin/src/services/fatsecret.ts` | FatSecret API клиент |
| `aifood-plugin/src/services/database.ts` | PostgreSQL репозиторий |
| `aifood-plugin/src/tools/log-food.ts` | Основной tool логирования |

## Конфигурация

В `~/.openclaw/openclaw.json`:
```json
{
  "plugins": {
    "entries": {
      "aifood": {
        "config": {
          "fatsecretClientId": "YOUR_CLIENT_ID",
          "fatsecretClientSecret": "YOUR_SECRET",
          "databaseUrl": "postgresql://localhost:5432/aifood"
        }
      }
    }
  }
}
```

## Архив

Старые Python сервисы сохранены в `_archive/`:
- `_archive/services/` — FastAPI, Telegram bot, MCP
- `_archive/docker-compose.yml` — Docker конфиги

## Правила

@import rules/safety.md
@import rules/code-style.md
@import rules/testing.md
@import rules/architecture.md
@import rules/dev-workflow.md
