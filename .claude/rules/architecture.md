# Architecture Rules

## OpenClaw Plugin Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      OpenClaw                            │
│  (WhatsApp, Telegram, Discord, Slack, Signal, iMessage) │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   AiFood Plugin                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                   Tools                          │   │
│  │  log_food │ search_food │ daily_report │ goals  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │                 Services                         │   │
│  │        FatSecretClient │ DatabaseService        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ PostgreSQL│   │ FatSecret │   │  Skill    │
       │    DB     │   │    API    │   │  Prompts  │
       └───────────┘   └───────────┘   └───────────┘
```

## Компоненты

| Компонент | Путь | Назначение |
|-----------|------|------------|
| Plugin Entry | `src/index.ts` | Регистрация tools в OpenClaw API |
| Tools | `src/tools/*.ts` | Обработчики для AI |
| Services | `src/services/*.ts` | Бизнес-логика и API клиенты |
| Types | `src/types/index.ts` | TypeScript интерфейсы |
| Skill | `skills/nutrition-advisor/SKILL.md` | Промпт для AI-советника |

## OpenClaw Tool Pattern

```typescript
export function createMyTool(service: MyService) {
  return {
    name: 'my_tool',
    description: 'What this tool does - used by AI to decide when to call it',
    parameters: {
      type: 'object',
      properties: {
        param1: { type: 'string', description: 'Description for AI' },
        param2: { type: 'number', description: 'Optional param' },
      },
      required: ['param1'],
    },
    handler: async (params: MyParams, ctx: { odentity: string }) => {
      // ctx.odentity - user identity from OpenClaw
      const result = await service.doSomething(params, ctx.odentity);

      return {
        success: true,
        message: 'Human-readable result',
        data: result,
      };
    },
  };
}
```

## Service Pattern

```typescript
export class MyService {
  constructor(config: ServiceConfig) {
    // Initialize connections
  }

  async doSomething(input: Input): Promise<Output> {
    // Business logic
  }

  async close(): Promise<void> {
    // Cleanup connections
  }
}
```

## Database Schema

```sql
-- Food log entries
CREATE TABLE food_log_entry (
  id BIGSERIAL PRIMARY KEY,
  odentity VARCHAR(255) NOT NULL,      -- OpenClaw user identity
  food_id VARCHAR(255),                 -- FatSecret food ID
  food_name VARCHAR(500) NOT NULL,
  calories NUMERIC(10, 2) NOT NULL,
  protein NUMERIC(10, 2),
  carbohydrates NUMERIC(10, 2),
  fat NUMERIC(10, 2),
  meal_type VARCHAR(20),
  consumed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_deleted BOOLEAN DEFAULT FALSE
);

-- User goals
CREATE TABLE user_goals (
  odentity VARCHAR(255) PRIMARY KEY,
  target_calories INTEGER,
  target_protein INTEGER,
  target_carbs INTEGER,
  target_fat INTEGER,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Skill Format (SKILL.md)

```markdown
---
name: skill-name
description: What the skill does
user-invocable: true
metadata: {"openclaw": {"emoji": "🥗"}}
---

# Skill Name

Instructions for the AI when this skill is active.

## Capabilities
- What tools to use
- How to respond

## Guidelines
- Behavior rules
```

## Error Handling

```typescript
handler: async (params, ctx) => {
  try {
    const result = await service.doSomething(params);
    return { success: true, data: result };
  } catch (error) {
    console.error('Tool error:', error);
    return {
      success: false,
      message: 'User-friendly error message',
    };
  }
}
```

## Configuration

Plugin config via `openclaw.plugin.json`:
```json
{
  "id": "plugin-id",
  "name": "Plugin Name",
  "configSchema": {
    "type": "object",
    "properties": {
      "apiKey": { "type": "string" },
      "databaseUrl": { "type": "string" }
    },
    "required": ["apiKey"]
  }
}
```

User config via `~/.openclaw/openclaw.json`:
```json
{
  "plugins": {
    "entries": {
      "plugin-id": {
        "config": {
          "apiKey": "value",
          "databaseUrl": "postgresql://..."
        }
      }
    }
  }
}
```
