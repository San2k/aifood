# OpenClaw Setup Guide for AiFood

Comprehensive guide to configuring OpenClaw for the AiFood nutrition tracking plugin.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Model Selection](#model-selection)
- [Telegram Setup](#telegram-setup)
- [Plugin Configuration](#plugin-configuration)
- [Troubleshooting](#troubleshooting)

## Overview

OpenClaw is a multi-platform AI assistant framework that enables AiFood to work across Telegram, WhatsApp, Discord, and other messaging platforms.

**Key Components:**
- **Gateway**: Handles messaging platform connections
- **Agent**: Processes messages using AI models
- **Plugins**: Extend functionality (AiFood is a plugin)

## Installation

### Prerequisites

- Linux/macOS (Windows via WSL)
- Node.js 18+ (for plugin development)
- Internet connection

### Install OpenClaw CLI

```bash
# Install via installer script
curl -fsSL https://openclaw.com/install.sh | sh

# Verify installation
openclaw --version

# Expected output: openclaw 2026.2.25 or later
```

### Initialize Configuration

```bash
# Run interactive configuration wizard
openclaw configure

# This creates ~/.openclaw/openclaw.json
```

## Configuration

### Main Config File

Location: `~/.openclaw/openclaw.json`

**Minimal configuration:**

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.0-flash-exp"
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN",
      "dmPolicy": "open"
    }
  }
}
```

### Agent Auth Configuration

Location: `~/.openclaw/agents/main/agent/auth.json`

```json
{
  "google": {
    "type": "api_key",
    "key": "YOUR_GOOGLE_AI_API_KEY"
  }
}
```

Get API key: https://aistudio.google.com/apikey

## Model Selection

OpenClaw supports multiple AI providers. For AiFood, we recommend:

### Recommended: Google Gemini (Free Tier)

**Why Gemini:**
- ✅ Fast response times (1-3 seconds)
- ✅ Generous free tier (1,500 req/day)
- ✅ Good tool/function calling support
- ✅ No GPU required

**Configuration:**

```json
{
  "auth": {
    "profiles": {
      "google:default": {
        "provider": "google",
        "mode": "api_key"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "google/gemini-2.0-flash-exp",
        "fallbacks": ["google/gemini-2.0-flash"]
      }
    }
  }
}
```

### Alternative: Groq (Free, Fast)

**Why Groq:**
- ✅ Extremely fast (500+ tokens/sec)
- ✅ Free tier: 30 req/min
- ✅ GPU-powered inference

**Configuration:**

1. Get API key: https://console.groq.com/keys

2. Update `auth.json`:
```json
{
  "groq": {
    "type": "api_key",
    "key": "YOUR_GROQ_API_KEY"
  }
}
```

3. Update `openclaw.json`:
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "groq/llama-3.1-70b-versatile"
      }
    }
  }
}
```

### Alternative: Local Ollama (Privacy)

**Why Ollama:**
- ✅ 100% private (runs locally)
- ✅ No API costs
- ⚠️ Requires powerful CPU or GPU
- ⚠️ Slower on CPU-only servers

**Installation:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5:7b-instruct

# Start Ollama service
systemctl start ollama
```

**Configuration:**

```json
{
  "auth": {
    "profiles": {
      "ollama:default": {
        "provider": "ollama",
        "mode": "api_key"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen2.5:7b-instruct",
        "fallbacks": ["google/gemini-2.0-flash-exp"]
      }
    }
  }
}
```

Update `~/.openclaw/agents/main/agent/auth.json`:

```json
{
  "ollama": {
    "type": "api_key",
    "key": "ollama-local",
    "baseUrl": "http://127.0.0.1:11434"
  },
  "google": {
    "type": "api_key",
    "key": "YOUR_GOOGLE_API_KEY"
  }
}
```

## Telegram Setup

### 1. Create Bot

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Follow prompts to set name and username
4. Copy the bot token (looks like `123456:ABC-DEF...`)

### 2. Configure Bot

Edit `~/.openclaw/openclaw.json`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN_HERE",
      "dmPolicy": "open",
      "groupPolicy": "allowlist",
      "streaming": "partial",
      "allowFrom": ["*"]
    }
  }
}
```

**Parameters explained:**

- `enabled`: Enable Telegram integration
- `botToken`: Your bot token from BotFather
- `dmPolicy`: `"open"` = anyone can DM bot
- `groupPolicy`: `"allowlist"` = only allowed groups
- `streaming`: `"partial"` = streaming responses
- `allowFrom`: `["*"]` = allow all users

### 3. Test Bot

```bash
# Start OpenClaw gateway
openclaw gateway run

# Or if using systemd:
sudo systemctl restart openclaw-gateway
```

Open Telegram and send `/start` to your bot.

## Plugin Configuration

### Install AiFood Plugin

```bash
# From repository root
cd aifood-plugin

# Build plugin
npm install
npm run build

# Install to OpenClaw
openclaw plugins install .
```

### Configure Plugin

Add plugin config to `~/.openclaw/openclaw.json`:

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

### Get FatSecret Credentials

1. Go to https://platform.fatsecret.com/api/
2. Sign up for developer account
3. Create new application
4. Copy Client ID and Client Secret

## Performance Optimization

### Memory Management

For servers with limited RAM:

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 2
    }
  }
}
```

**Parameters:**

- `compaction.mode`:
  - `"safeguard"`: Automatic context compression
  - `"off"`: No compression (may use more memory)
- `maxConcurrent`: Max parallel conversations

### Model Parameters

For faster responses with Ollama:

Create Modelfile:

```
FROM qwen2.5:7b-instruct

PARAMETER num_ctx 4096
PARAMETER num_predict 512
PARAMETER temperature 0.25
```

Create model:

```bash
ollama create qwen-optimized -f Modelfile
```

Update config:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen-optimized"
      }
    }
  }
}
```

## Troubleshooting

### Bot Not Responding

**Check 1: Gateway Running**

```bash
# Check status
sudo systemctl status openclaw-gateway

# View logs
journalctl -u openclaw-gateway -f
```

**Check 2: Bot Token Valid**

```bash
# Test token
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Should return bot info
```

**Check 3: Plugin Loaded**

```bash
# Check logs for plugin
journalctl -u openclaw-gateway | grep -i aifood

# Should see: "AiFood: Plugin registered"
```

### "Model Not Found" Error

**Solution**: Verify model name and API key

```bash
# Check agent auth
cat ~/.openclaw/agents/main/agent/auth.json

# Check model config
cat ~/.openclaw/openclaw.json | grep -A 5 '"model"'
```

### Slow Responses (Ollama)

**Problem**: 46k+ token prompts on CPU are slow

**Solutions**:

1. **Use Gemini** (recommended):
   ```json
   {
     "agents": {
       "defaults": {
         "model": {
           "primary": "google/gemini-2.0-flash-exp"
         }
       }
     }
   }
   ```

2. **Get GPU server** (if must use Ollama):
   - Min: NVIDIA GTX 1060 6GB
   - Recommended: RTX 4000 Ada or A10

3. **Use smaller model**:
   ```bash
   ollama pull phi3.5:3.8b
   ```

### Plugin Not Loading

```bash
# List plugins
openclaw plugins list

# Reinstall
openclaw plugins uninstall aifood
cd /opt/aifood/aifood-plugin
npm run build
openclaw plugins install .

# Restart gateway
sudo systemctl restart openclaw-gateway
```

### Database Connection Failed

```bash
# Test PostgreSQL
psql -h localhost -p 5433 -U aifood -d aifood -c "SELECT 1;"

# Check config
cat ~/.openclaw/openclaw.json | grep databaseUrl

# Verify password matches
```

## Advanced Configuration

### Multiple Channels

Enable WhatsApp, Discord, etc.:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "..."
    },
    "whatsapp": {
      "enabled": true,
      "phoneNumber": "+1234567890"
    },
    "discord": {
      "enabled": true,
      "botToken": "..."
    }
  }
}
```

### Custom System Prompt

Edit `~/.openclaw/agents/main/agent/prompt.md`:

```markdown
You are a helpful AI nutrition assistant.

# Capabilities
- Log food entries
- Search nutrition database
- Provide daily/weekly reports
- Set and track nutrition goals

# Guidelines
- Always be encouraging and supportive
- Use metric units (grams, kcal)
- Respond in user's language
```

### Session Management

Control conversation history:

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard"
      }
    }
  }
}
```

## Resources

- OpenClaw Docs: https://docs.openclaw.ai
- Gemini AI Studio: https://aistudio.google.com
- Groq Console: https://console.groq.com
- FatSecret API: https://platform.fatsecret.com

---

Last Updated: March 2026
