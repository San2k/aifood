# LLM Gateway

Self-hosted LLM Gateway with Token Optimization for OpenClaw. Provides an OpenAI-compatible API that proxies requests to Gemini API with advanced token optimization features.

## Features

- **OpenAI-Compatible API**: Standard `/v1/chat/completions` endpoint
- **Gemini Integration**: Translates requests to Gemini OpenAI-compatible format
- **Token Optimization**: History trimming, summarization, RAG budget limiting
- **Response Caching**: Redis-based caching for deterministic queries
- **Quota Management**: Per-tenant daily token limits and monthly budgets
- **Observability**: Structured JSON logging with winston
- **Streaming Support**: Server-Sent Events (SSE) for streaming responses
- **Error Handling**: Automatic retries with exponential backoff

## Architecture

```
OpenClaw Gateway (18789)
         ↓
  LLM Gateway (9000) ← OpenAI-compatible API
         ↓
  Gemini API (OpenAI-compatible endpoint)
```

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Build

```bash
npm run build
```

### 4. Run

```bash
# Development mode with auto-reload
npm run dev

# Production mode
npm start
```

## API Usage

### Chat Completions (Non-Streaming)

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3-flash-preview",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### Chat Completions (Streaming)

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3-flash-preview",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true,
    "max_tokens": 500
  }'
```

### Health Check

```bash
curl http://localhost:9000/health
```

Response:
```json
{
  "status": "ok",
  "uptime": 123.45,
  "timestamp": 1234567890,
  "version": "1.0.0"
}
```

## Configuration

All configuration is done via environment variables in `.env`:

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_PORT` | `9000` | Server port |
| `GATEWAY_HOST` | `0.0.0.0` | Server host |

### Gemini

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | **required** | Gemini API key from Google AI Studio |
| `GEMINI_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` | Gemini OpenAI-compatible endpoint |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Default model for brief/standard profiles |
| `GEMINI_MODEL_PRO` | `gemini-3-flash-preview` | Model for analysis profile |
| `GEMINI_TIMEOUT` | `60000` | Request timeout in ms |
| `GEMINI_RETRIES` | `3` | Max retry attempts |

### Token Policy

| Variable | Default | Description |
|----------|---------|-------------|
| `HISTORY_WINDOW_TOKENS` | `12000` | Max tokens in history window |
| `HISTORY_WINDOW_MESSAGES` | `8` | Max messages to keep |
| `SUMMARY_TRIGGER_TOKENS` | `12000` | Trigger summarization at N tokens |
| `SUMMARY_TARGET_TOKENS` | `1000` | Compress summary to N tokens |
| `RAG_BUDGET_TOKENS` | `2000` | Max tokens for RAG context |

### Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_ENABLED` | `true` | Enable Redis caching |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |
| `REDIS_URL` | `redis://localhost:6379/1` | Redis connection URL |

### Quotas

| Variable | Default | Description |
|----------|---------|-------------|
| `QUOTA_DAILY_TOKENS` | `100000` | Daily token limit per tenant |
| `QUOTA_MONTHLY_USD` | `50` | Monthly USD budget per tenant |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `info` | Log level: debug, info, warn, error |
| `METRICS_ENABLED` | `false` | Enable Prometheus metrics |
| `TRACING_ENABLED` | `false` | Enable distributed tracing |

## Development

### Scripts

```bash
# Development mode with auto-reload
npm run dev

# Build TypeScript
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Run tests
npm test
```

### Project Structure

```
src/
├── index.ts                # Entry point
├── server.ts               # Fastify server setup
├── config/
│   └── index.ts            # Configuration loader
├── middleware/
│   ├── token-policy.ts     # Token optimization (TODO)
│   ├── auth.ts             # Authentication (TODO)
│   └── error-handler.ts    # Error handling (TODO)
├── providers/
│   ├── base-provider.ts    # Provider interface
│   ├── gemini-provider.ts  # Gemini adapter
│   └── factory.ts          # Provider factory (TODO)
├── services/
│   ├── logger.ts           # Winston logger
│   ├── token-counter.ts    # Token estimation (TODO)
│   ├── history-manager.ts  # History optimization (TODO)
│   ├── cache-service.ts    # Redis cache (TODO)
│   ├── quota-service.ts    # Quota tracking (TODO)
│   └── observability.ts    # Metrics (TODO)
├── routes/
│   └── chat-completions.ts # Chat completions endpoint
└── types/
    ├── openai.ts           # OpenAI API types
    └── config.ts           # Config types
```

## Docker

### Build Image

```bash
docker build -t llm-gateway .
```

### Run Container

```bash
docker run -d \
  --name llm-gateway \
  -p 9000:9000 \
  -e GEMINI_API_KEY=your_key_here \
  llm-gateway
```

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  llm-gateway:
    build: ./services/llm-gateway
    ports:
      - "9000:9000"
    environment:
      GATEWAY_PORT: 9000
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      GEMINI_MODEL: gemini-3-flash-preview
      REDIS_URL: redis://redis:6379/1
      LOG_LEVEL: info
    depends_on:
      - redis
```

## Logs

Logs are written to:
- `logs/combined.log` - All logs (JSON format)
- `logs/error.log` - Error logs only (JSON format)
- Console - Human-readable colored output

Example log entry:
```json
{
  "timestamp": "2026-03-03 19:34:00",
  "level": "info",
  "module": "chat-completions",
  "type": "chat_completion_response",
  "requestId": "req-1",
  "latency": 2534,
  "promptTokens": 6,
  "completionTokens": 2,
  "totalTokens": 13
}
```

## OpenClaw Integration

Update `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "gateway/standard"
      }
    }
  },
  "models": {
    "providers": {
      "gateway": {
        "baseUrl": "http://localhost:9000/v1",
        "api": "openai-completions",
        "models": [
          {
            "id": "brief",
            "name": "Brief Output (256-512 tokens)",
            "contextWindow": 100000,
            "maxTokens": 512
          },
          {
            "id": "standard",
            "name": "Standard Output (800-1200 tokens)",
            "contextWindow": 100000,
            "maxTokens": 1200
          }
        ]
      }
    }
  }
}
```

## Troubleshooting

### Gateway won't start

Check if port 9000 is already in use:
```bash
lsof -i :9000
```

Kill existing process:
```bash
pkill -f "node dist/index.js"
```

### Gemini API errors

1. Check API key is valid in `.env`
2. Verify model name is correct: `gemini-3-flash-preview`
3. Check base URL ends with `/`: `https://generativelanguage.googleapis.com/v1beta/openai/`

### Empty responses

If `message.content` is empty, increase `max_tokens` parameter.

### Cache not working

1. Ensure Redis is running on the configured URL
2. Check `CACHE_ENABLED=true` in `.env`
3. Only deterministic queries (temperature=0) are cached

## Roadmap

**Week 1: Core Gateway** ✅ COMPLETED
- [x] Project structure
- [x] TypeScript configuration
- [x] Config loader
- [x] Fastify server
- [x] Gemini provider adapter
- [x] Chat completions route
- [x] Health check endpoint

**Week 2: Token Policy Engine** (IN PROGRESS)
- [ ] Token counter service
- [ ] History manager (sliding window + summarization)
- [ ] Cache service (Redis)
- [ ] Quota service
- [ ] Token policy middleware

**Week 3: Observability + Integration**
- [ ] Observability service (metrics export)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Docker deployment
- [ ] OpenClaw integration

## License

MIT

## Links

- [Gemini OpenAI-Compatible API Documentation](https://ai.google.dev/gemini-api/docs/openai)
- [Google AI Studio (Get API Key)](https://aistudio.google.com/apikey)
