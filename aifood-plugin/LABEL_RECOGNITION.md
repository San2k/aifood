# 📸 Nutrition Label Recognition

Автоматическое распознавание этикеток продуктов с использованием PaddleOCR и Gemini Vision.

## Как работает

1. **Отправь фото** этикетки продукта через OpenClaw
2. **AI распознает** КБЖУ автоматически (OCR + Vision AI)
3. **Подтверди** порцию: "подтвердить 150г"
4. **Готово** - продукт записан в дневник питания

## Примеры использования

### Telegram/WhatsApp
```
Пользователь: [отправляет фото этикетки]
AI: 📊 Распознан продукт:

**Овсяное печенье**
Бренд: БрендНазвание

КБЖУ на 100г:
🔥 250 ккал
🥩 Белок: 12г
🍞 Углеводы: 30г
🧈 Жиры: 10г

📝 Метод: OCR

✅ Для подтверждения напишите: "подтвердить 150г"
❌ Для отмены: "отменить"

Пользователь: подтвердить 150г
AI: ✅ Записано: Овсяное печенье (150г)

Дневной итог: 1250 ккал
```

## Архитектура

```
OpenClaw Plugin (TypeScript)
  ↓ photoUrl
Agent API (FastAPI + LangGraph)
  ↓ image processing
OCR Service (PaddleOCR русский)
  ↓ OCR confidence check
Gemini Vision (fallback если OCR < 75%)
  ↓ validation
PostgreSQL (custom_products, label_scans)
  ↓ confirmation dialog (Redis)
User confirms → food_log_entry
```

## Tools

### 1. `log_food_from_photo`

Обрабатывает фото этикетки и показывает карточку подтверждения.

**Параметры:**
- `photoUrl` (required): URL фото этикетки
- `meal` (optional): breakfast, lunch, dinner, snack
- `date` (optional): YYYY-MM-DD

**Пример:**
```typescript
{
  "photoUrl": "https://example.com/label.jpg",
  "meal": "breakfast"
}
```

**Возвращает:**
```json
{
  "content": [{"type": "text", "text": "📊 Распознан продукт..."}],
  "details": {
    "success": true,
    "scan_id": "uuid",
    "product": {...},
    "awaitingConfirmation": true
  }
}
```

### 2. `confirm_food_from_photo`

Подтверждает распознанный продукт и логирует в food_log_entry.

**Параметры:**
- `grams` (required): количество грамм
- `meal` (optional): breakfast, lunch, dinner, snack

**Пример:**
```typescript
{
  "grams": 150,
  "meal": "breakfast"
}
```

**Возвращает:**
```json
{
  "content": [{"type": "text", "text": "✅ Записано: ..."}],
  "details": {
    "success": true,
    "entry_id": 123,
    "dailyTotals": {...}
  }
}
```

## Конфигурация

В `openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "aifood": {
        "config": {
          "databaseUrl": "postgresql://aifood:password@localhost:5433/aifood",
          "agentApiUrl": "http://localhost:8000"
        }
      }
    }
  }
}
```

## Требования

### Сервисы

1. **agent-api** (port 8000)
   - FastAPI + LangGraph
   - PostgreSQL (5433)
   - Redis (6379)

2. **ocr-service** (port 8001)
   - PaddleOCR с русским языком
   - Marker detection

3. **Gemini Vision API**
   - API key в `GEMINI_API_KEY`
   - Fallback при OCR confidence < 0.75

### База данных

Таблицы (миграция `001_add_label_recognition_tables.sql`):
- `custom_products` - распознанные продукты
- `label_scans` - история сканирований
- `food_log_entry.custom_product_id` - ссылка на кастомный продукт

## Workflow

### Обработка этикетки

1. **Download Image** (10%)
   - Загрузка с photoUrl в /tmp/aifood/uploads

2. **Preprocess Image** (20%)
   - Auto-rotate (EXIF)
   - Deskew (коррекция угла)
   - CLAHE (контраст)
   - Upscale (1400px)

3. **OCR Extract** (40%)
   - PaddleOCR lang='ru'
   - Marker detection

4. **Quality Check** (50%)
   - Confidence >= 0.75?
   - Markers >= 2?

5a. **Parse OCR** (60%) - если качество хорошее
   - Regex extraction
   - Comma → dot
   - Per-serving → per-100g

5b. **Vision Fallback** (60%) - если OCR плохое
   - Gemini Vision API
   - Structured JSON prompt

6. **Validate** (70%)
   - Range checks
   - kJ → kcal
   - Sanity checks

7. **Create Product** (85%)
   - INSERT custom_products

8. **Store Scan** (100%)
   - INSERT label_scans
   - Redis TTL 30 минут
   - Status: pending_confirmation

### Подтверждение

1. User sends "подтвердить 150г"
2. Plugin вызывает `confirm_food_from_photo(grams=150)`
3. Agent API `/v1/confirm_message`
4. Проверяет Redis pending scan
5. Рассчитывает nutrition для порции
6. INSERT food_log_entry
7. UPDATE label_scans status='confirmed'
8. Clear Redis
9. Возврат дневных totals

## Примеры ошибок

### OCR failed
```
📊 Распознан продукт:
...
📝 Метод: Vision AI

(автоматический fallback на Gemini)
```

### Timeout
```
Обработка занимает больше времени, чем ожидалось. Попробуйте позже.
```

### No pending scan
```
Нет ожидающего подтверждения сканирования
```

## Testing

```bash
# Build plugin
cd aifood-plugin
npm run build

# Install in OpenClaw
openclaw plugins install ./aifood-plugin

# Test via OpenClaw
# 1. Send photo of nutrition label
# 2. AI calls log_food_from_photo
# 3. User: "подтвердить 150г"
# 4. AI calls confirm_food_from_photo
# 5. Check database: SELECT * FROM food_log_entry ORDER BY created_at DESC LIMIT 1;
```

## Production Deployment

### Server: 199.247.30.52

```bash
# Build Docker images
cd /root/aifood
docker-compose build agent-api ocr-service

# Start services
docker-compose up -d agent-api ocr-service redis

# Check logs
docker-compose logs -f agent-api
docker-compose logs -f ocr-service

# Test health
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql+asyncpg://aifood:password@postgres:5432/aifood
REDIS_URL=redis://redis:6379/0
OCR_SERVICE_URL=http://ocr-service:8001
GEMINI_API_KEY=your_api_key_here
AGENT_API_URL=http://agent-api:8000
```

## Success Metrics

- ✅ OCR confidence >= 75% на 80% тестовых этикеток
- ✅ Vision fallback срабатывает корректно
- ✅ Avg processing time < 5 секунд
- ✅ Comma→dot, kJ→kcal конверсии работают
- ✅ User confirmation обязательно
- ✅ 0 hallucinated values (только реальные данные)

## Troubleshooting

### Plugin не видит agentApiUrl
```bash
# Check OpenClaw config
cat ~/.openclaw/openclaw.json | grep agentApiUrl

# Should return:
"agentApiUrl": "http://localhost:8000"
```

### Agent API недоступен
```bash
# Check service
curl http://localhost:8000/health

# Check logs
docker-compose logs agent-api
```

### OCR Service недоступен
```bash
curl http://localhost:8001/health
docker-compose logs ocr-service
```

### Redis нет pending scan
```bash
# Check Redis
docker exec -it aifood-redis redis-cli
KEYS pending_scan:*
GET pending_scan:user:default
```

---

**Версия:** 1.0.0
**Статус:** Week 4 - Plugin Integration Complete
