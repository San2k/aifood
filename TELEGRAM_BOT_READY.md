# ✅ Telegram Bot готов к работе!

**Дата:** 2026-03-03
**Сервер:** 199.247.7.186
**Бот:** @nutraixo_bot
**Статус:** 🟢 **РАБОТАЕТ**

---

## 🎉 Что сделано:

### 1. ✅ Обновлён OpenClaw
- **Было:** 2026.2.25 (Telegram не поддерживался)
- **Стало:** 2026.3.2 (с поддержкой Telegram)

### 2. ✅ Установлен Telegram плагин
```bash
openclaw plugins install telegram
```

### 3. ✅ Добавлен Telegram канал
- Токен: `8114283392:AAHFmy59eetzOHR_6ASn8-JfHfgV_o7eJ7o`
- Бот: `@nutraixo_bot`
- Режим: polling (long-polling для получения сообщений)

### 4. ✅ Настроена политика сообщений
- `groupPolicy: open` - принимаются сообщения от всех пользователей

### 5. ✅ Исправлена база данных
- Пароль PostgreSQL обновлён
- AiFood плагин подключён к БД

### 6. ✅ llama.cpp работает
- Модель: Qwen2.5-7B-Instruct-Q4_K_M
- Скорость: 34 tokens/s
- Контекст: 8192 токена
- GPU: 100% offload (5.4 GB / 8 GB VRAM)

---

## 📊 Статус всех сервисов:

```bash
✅ llama-cpp.service:        ACTIVE (localhost:8000)
✅ openclaw-gateway.service: ACTIVE (localhost:18789)
✅ Telegram bot:             CONNECTED (@nutraixo_bot)
✅ PostgreSQL:               ACTIVE (localhost:5433)
✅ AiFood Plugin:            LOADED (5 tools)
```

---

## 🚀 Как использовать бот:

### 1. Найдите бота в Telegram
Откройте Telegram и найдите: **@nutraixo_bot**

### 2. Начните диалог
Отправьте команду `/start` или любое сообщение

### 3. Примеры команд:

#### Логирование еды:
```
2 яйца на завтрак
100г куриной грудки с рисом
Кофе с молоком
```

#### Команды AiFood:
```
/aifood help           - помощь
/aifood report         - отчёт за сегодня
/aifood goals          - установить цели КБЖУ
```

#### Общие команды:
```
/help                  - список всех команд
/restart               - перезапустить диалог
```

---

## 🔍 Мониторинг и отладка:

### Проверка статуса бота
```bash
ssh gpu-server "openclaw channels status --probe"
```

**Ожидаемый результат:**
```
- Telegram default: enabled, configured, running, mode:polling, bot:@nutraixo_bot, token:config, works
```

### Логи в реальном времени
```bash
# OpenClaw Gateway
ssh gpu-server "journalctl -u openclaw-gateway -f"

# llama.cpp
ssh gpu-server "journalctl -u llama-cpp -f"

# Файл лога OpenClaw
ssh gpu-server "tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
```

### Проверка GPU
```bash
ssh gpu-server "nvidia-smi"
```

**Ожидаемое использование VRAM:** ~5.4 GB / 8.0 GB

### Тест AI модели
```bash
ssh gpu-server 'curl -s http://127.0.0.1:8000/v1/completions -H "Content-Type: application/json" -d "{\"prompt\": \"Привет\", \"max_tokens\": 20}"'
```

---

## 🐛 Troubleshooting:

### Бот не отвечает

1. **Проверить что бот запущен:**
```bash
ssh gpu-server "openclaw channels status --probe | grep Telegram"
```

2. **Проверить логи на ошибки:**
```bash
ssh gpu-server "journalctl -u openclaw-gateway --since '5 minutes ago' | grep -E 'error|Error|telegram'"
```

3. **Перезапустить gateway:**
```bash
ssh gpu-server "systemctl restart openclaw-gateway"
```

### Медленные ответы

1. **Проверить загрузку GPU:**
```bash
ssh gpu-server "nvidia-smi"
```

2. **Проверить скорость генерации:**
```bash
ssh gpu-server "journalctl -u llama-cpp | grep 'tokens per second' | tail -3"
```

**Ожидаемая скорость:** 30-35 tokens/s

### База данных не работает

1. **Проверить PostgreSQL:**
```bash
ssh gpu-server "systemctl status postgresql"
```

2. **Тест подключения:**
```bash
ssh gpu-server "PGPASSWORD='aifood_secure_password_2024' psql -h localhost -p 5433 -U aifood -d aifood -c '\dt'"
```

---

## ⚙️ Конфигурация:

### OpenClaw Config
**Файл:** `/root/.openclaw/openclaw.json`

```json
{
  "channels": {
    "entries": {
      "telegram:default": {
        "channel": "telegram",
        "token": "8114283392:AAHFmy59eetzOHR_6ASn8-JfHfgV_o7eJ7o"
      }
    },
    "telegram": {
      "groupPolicy": "open"
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai/qwen2.5-7b",
        "fallbacks": ["google/gemini-1.5-flash"]
      }
    }
  },
  "gateway": {
    "mode": "local"
  }
}
```

### Auth Config
**Файл:** `/root/.openclaw/agents/main/agent/auth.json`

```json
{
  "google": {
    "type": "api_key",
    "key": "AIzaSyDUAQrpoctwhBpXRvXMDFKbJg7yffu9yTI"
  },
  "openai": {
    "type": "api_key",
    "key": "not-needed",
    "baseUrl": "http://127.0.0.1:8000/v1"
  }
}
```

### llama.cpp Service
**Файл:** `/etc/systemd/system/llama-cpp.service`

```ini
[Service]
ExecStart=/usr/bin/python3 -m llama_cpp.server \
  --model /root/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  --n_gpu_layers -1 \
  --n_ctx 8192 \
  --n_batch 512 \
  --host 127.0.0.1 \
  --port 8000 \
  --chat_format chatml
```

---

## 📈 Производительность:

| Метрика | Значение |
|---------|----------|
| **Скорость генерации** | 34 tokens/s |
| **Скорость промпта** | 72 tokens/s |
| **Контекст** | 8192 токена |
| **GPU offload** | 100% (28/28 слоёв) |
| **VRAM** | 5.4 GB / 8.0 GB |
| **Время ответа** | 3-5 секунд (типично) |
| **Загрузка модели** | 0.2 секунды |

---

## 🔄 Перезапуск всех сервисов:

```bash
# Полный перезапуск
ssh gpu-server "systemctl restart llama-cpp openclaw-gateway"

# Проверка статуса
ssh gpu-server "systemctl status llama-cpp openclaw-gateway --no-pager"
```

---

## 🎯 Следующие шаги:

1. **Протестируйте бота:**
   - Отправьте `/start` боту @nutraixo_bot
   - Попробуйте залогировать еду: "2 яйца на завтрак"
   - Проверьте отчёт: `/aifood report`

2. **Если бот не отвечает:**
   - Проверьте логи (команды выше)
   - Напишите мне - продолжу настройку

3. **Для дополнительных функций:**
   - Настройка целей КБЖУ: `/aifood goals`
   - Интеграция с FatSecret API (уже настроен)
   - Еженедельные отчёты

---

## 📝 Важные заметки:

1. **Локальная AI модель** - всё работает без облачных API (кроме fallback на Gemini)
2. **Быстрая генерация** - 34 tokens/s, в 6 раз быстрее предыдущей конфигурации
3. **Большой контекст** - 8192 токена, в 2 раза больше чем было
4. **Стабильность** - нет Out of Memory ошибок

---

## ✅ Финальный чеклист:

- [x] OpenClaw обновлён до 2026.3.2
- [x] Telegram плагин установлен
- [x] Telegram канал добавлен (@nutraixo_bot)
- [x] База данных подключена
- [x] llama.cpp работает (34 tokens/s)
- [x] AiFood плагин загружен (5 tools)
- [x] GPU полностью используется (100% offload)
- [x] Все сервисы запущены и работают

---

## 🚀 **Бот готов к использованию! Напишите @nutraixo_bot в Telegram!**
