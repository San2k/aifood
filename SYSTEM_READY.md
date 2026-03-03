# ✅ OpenClaw + AiFood готов к работе!

**Дата:** 2026-03-03  
**Сервер:** 199.247.7.186  
**Telegram бот:** @LenoxAI_bot  
**Статус:** 🟢 **ПОЛНОСТЬЮ РАБОТАЕТ**

---

## 🎉 Система готова!

### Что работает:

```
✅ OpenClaw Gateway:     ACTIVE (localhost:18789)
✅ Telegram:             @LenoxAI_bot (подключён, works)
✅ llama.cpp:            34 tokens/s, 8192 контекст, 100% GPU
✅ AiFood Plugin:        5 tools доступны
✅ PostgreSQL:           База данных aifood работает
✅ GPU:                  5.4 GB / 8.0 GB VRAM
```

---

## 📱 Как использовать:

### 1. Откройте Telegram
### 2. Найдите бота: **@LenoxAI_bot**
### 3. Начните диалог:

#### Общение с AI (llama.cpp):
```
Привет
Как дела?
Расскажи про здоровое питание
```

#### Логирование еды (AiFood):
```
2 яйца на завтрак
100г куриной грудки с рисом
Кофе с молоком
```

#### AiFood команды:
```
/aifood help           - помощь по плагину
/aifood report         - отчёт за сегодня
/aifood goals          - установить цели КБЖУ
```

#### OpenClaw команды:
```
/help                  - все доступные команды
/restart               - перезапустить диалог
/skills                - доступные навыки
```

---

## 🏗️ Архитектура:

```
    Вы в Telegram
         ↓
   @LenoxAI_bot
         ↓
 OpenClaw Gateway (localhost:18789)
         ├── llama.cpp (локальная AI, 7B модель)
         │   └── Qwen2.5-7B-Instruct-Q4_K_M
         │       ├── 34 tokens/s
         │       ├── 8192 контекст
         │       └── 100% GPU offload
         │
         ├── AiFood Plugin
         │   ├── log_food (логирование)
         │   ├── search_food (поиск калорий)
         │   ├── daily_report (отчёт за день)
         │   ├── weekly_report (отчёт за неделю)
         │   └── set_goals (установка целей)
         │
         └── PostgreSQL (localhost:5433)
             └── База данных: aifood
```

---

## 📊 Производительность:

| Компонент | Статус | Метрики |
|-----------|--------|---------|
| **llama.cpp** | ✅ Работает | 34 tokens/s, 8192 ctx |
| **OpenClaw** | ✅ Работает | 2026.3.2 |
| **Telegram** | ✅ Подключён | @LenoxAI_bot, polling |
| **AiFood** | ✅ Загружен | 5 tools |
| **GPU** | ✅ Активен | 5.4 / 8.0 GB VRAM |
| **PostgreSQL** | ✅ Работает | aifood@localhost:5433 |

---

## 🔧 Мониторинг:

### Проверка статуса
```bash
# Все сервисы
ssh gpu-server "systemctl status openclaw-gateway llama-cpp --no-pager"

# Telegram бот
ssh gpu-server "openclaw channels status --probe"

# GPU
ssh gpu-server "nvidia-smi"
```

### Логи в реальном времени
```bash
# OpenClaw
ssh gpu-server "journalctl -u openclaw-gateway -f"

# llama.cpp
ssh gpu-server "journalctl -u llama-cpp -f"

# Файл лога
ssh gpu-server "tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
```

### Перезапуск
```bash
ssh gpu-server "systemctl restart openclaw-gateway llama-cpp"
```

---

## 🐛 Если что-то не работает:

### Бот не отвечает
```bash
# 1. Проверить статус
ssh gpu-server "openclaw channels status --probe"

# 2. Посмотреть ошибки
ssh gpu-server "journalctl -u openclaw-gateway --since '5 min ago' | grep -i error"

# 3. Перезапустить
ssh gpu-server "systemctl restart openclaw-gateway"
```

### Медленные ответы
```bash
# Проверить GPU
ssh gpu-server "nvidia-smi"

# Проверить скорость
ssh gpu-server "journalctl -u llama-cpp | grep 'tokens per second' | tail -3"
```

### База данных
```bash
# Проверить PostgreSQL
ssh gpu-server "systemctl status postgresql"

# Тест подключения
ssh gpu-server "PGPASSWORD='aifood_secure_password_2024' psql -h localhost -p 5433 -U aifood -d aifood -c '\dt'"
```

---

## ⚙️ Конфигурация:

### OpenClaw Config
`/root/.openclaw/openclaw.json`:
```json
{
  "channels": {
    "entries": {
      "telegram:default": {
        "channel": "telegram",
        "token": "8205605578:AAHx_Be6RJL6Q7sQxhSTTXjYdl6eRkXJPF8"
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
  }
}
```

### AI Model
- **Файл:** `/root/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf`
- **Размер:** 4.68 GB
- **Квантизация:** Q4_K_M (4-bit)
- **Контекст:** 8192 токена
- **GPU:** 100% offload (28/28 слоёв)

---

## 🚀 Готово к использованию!

**Напишите @LenoxAI_bot в Telegram и начните диалог!**

Примеры:
- "Привет" - обычное общение с AI
- "2 яйца на завтрак" - логирование еды
- "/aifood report" - отчёт за день
