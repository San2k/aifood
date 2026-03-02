# План развертывания Ollama на новом сервере

## Сравнение серверов

| Характеристика | Старый (199.247.30.52) | Новый (199.247.7.186) |
|----------------|------------------------|----------------------|
| CPU | 6 ядер (Xeon Skylake) | 4 ядра (Core Broadwell) |
| RAM | 15GB (доступно 13GB) | 19GB (доступно 18GB) |
| Swap | 8GB | 8GB |
| Disk | - | 338GB (306GB free) |
| Текущая модель | qwen-optimized:latest | google/gemini-2.0-flash-exp |

## Текущая конфигурация на старом сервере

### Модель
- **Primary**: `ollama/qwen-optimized:latest` (локальная)
- **Fallback**: `google/gemini-2.0-flash-exp` (облачная)
- **Size**: 4.7 GB
- **Base model**: qwen2.5:7b-instruct

### Параметры Modelfile
```
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 512
```

### OpenClaw настройки
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen-optimized:latest",
        "fallbacks": ["google/gemini-2.0-flash-exp"]
      },
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 4
    }
  }
}
```

## Адаптация для нового сервера

### Преимущества нового сервера
✅ **Больше RAM** (19GB vs 15GB) - можно использовать ту же модель без проблем
✅ **Больше свободного места** (306GB vs неизвестно)
✅ **8GB Swap** - достаточно для резервирования

### Ограничения
⚠️ **Меньше CPU ядер** (4 vs 6) - inference будет чуть медленнее
⚠️ **Нет GPU** - используется CPU inference

### Рекомендуемые настройки

#### 1. Ollama Model
Используем ту же модель `qwen-optimized` с теми же параметрами:
```
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 512
```

**Почему не меняем:**
- 4.7GB модель отлично помещается в 19GB RAM
- num_ctx 4096 - разумный context window (не слишком большой)
- temperature 0.25 - детерминистичные ответы для бота

#### 2. OpenClaw Configuration
```json
{
  "auth": {
    "profiles": {
      "google:default": {
        "provider": "google",
        "mode": "api_key"
      },
      "ollama:default": {
        "provider": "ollama",
        "mode": "api_key"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen-optimized:latest",
        "fallbacks": ["google/gemini-2.0-flash-exp"]
      },
      "models": {
        "ollama/qwen-optimized:latest": {},
        "google/gemini-2.0-flash-exp": {}
      },
      "workspace": "/root/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 3
    }
  }
}
```

**Изменения:**
- ✅ `maxConcurrent: 3` (было 4) - т.к. меньше CPU ядер
- ✅ Остальное без изменений

#### 3. auth.json
```json
{
  "google": {
    "type": "api_key",
    "key": "AIzaSyA1H3vLr_G2uc6a5d2cJdyOgA9gxy7UpQE"
  }
}
```
(Ollama не требует auth, работает на localhost:11434)

## Этапы развертывания

### Шаг 1: Установка Ollama (5 минут)
```bash
# Установка
curl -fsSL https://ollama.com/install.sh | sh

# Проверка
systemctl status ollama
ollama --version
```

### Шаг 2: Загрузка базовой модели (10-15 минут)
```bash
# Скачать qwen2.5:7b-instruct (~4.7GB)
ollama pull qwen2.5:7b-instruct

# Проверка
ollama list
```

### Шаг 3: Создание оптимизированной модели (1 минута)
```bash
# Создать Modelfile
cat > /tmp/Modelfile << 'EOF'
FROM qwen2.5:7b-instruct

PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 512

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

# Создать модель
ollama create qwen-optimized:latest -f /tmp/Modelfile

# Проверка
ollama list
ollama run qwen-optimized:latest "Hello, how are you?" --verbose
```

### Шаг 4: Обновление OpenClaw конфигурации (2 минуты)
```bash
# Бэкап текущего конфига
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.backup

# Обновить openclaw.json (добавить auth profiles и изменить model)
# Используем jq для точечного обновления
```

### Шаг 5: Перезапуск OpenClaw (1 минута)
```bash
# Перезапустить gateway
systemctl restart openclaw-gateway

# Проверить статус
systemctl status openclaw-gateway
journalctl -u openclaw-gateway -f
```

### Шаг 6: Тестирование (5 минут)
```bash
# Отправить тестовое сообщение в Telegram бот
# Проверить что:
# 1. Ответ приходит от ollama/qwen-optimized
# 2. Скорость ответа приемлемая (10-30 сек на CPU)
# 3. Качество ответов адекватное

# Проверить логи Ollama
journalctl -u ollama -f

# Проверить использование ресурсов
htop
```

## Ожидаемая производительность

### На старом сервере (6 CPU, 15GB RAM)
- Первый токен: ~5-10 секунд
- Генерация: ~10-20 токенов/сек
- Общее время ответа: 15-40 секунд

### На новом сервере (4 CPU, 19GB RAM)
- Первый токен: ~7-15 секунд (чуть медленнее)
- Генерация: ~7-15 токенов/сек (чуть медленнее)
- Общее время ответа: 20-50 секунд
- **Fallback**: если слишком медленно, автоматически переключится на Gemini

## Мониторинг

### Команды для мониторинга
```bash
# Ollama статус
systemctl status ollama

# Логи Ollama
journalctl -u ollama -f

# OpenClaw логи
journalctl -u openclaw-gateway -f

# Использование ресурсов
htop

# Ollama процессы
ps aux | grep ollama

# Список моделей
ollama list

# Тест модели
ollama run qwen-optimized:latest "Привет, как дела?"
```

### Признаки проблем
- ❌ Ollama service не запускается → проверить `journalctl -u ollama`
- ❌ Модель загружается >2 минут → нормально при первом запуске
- ❌ Ответы >60 секунд → возможно нужно уменьшить num_ctx или использовать Gemini fallback
- ❌ Out of memory → увеличить swap или уменьшить maxConcurrent

## Альтернативные варианты

### Если Ollama слишком медленный:
**Вариант 1**: Использовать только Gemini (бесплатный tier)
```json
{
  "model": {
    "primary": "google/gemini-2.0-flash-exp"
  }
}
```

**Вариант 2**: Groq (быстрый облачный, бесплатный tier)
```json
{
  "model": {
    "primary": "groq/llama-3.1-70b-versatile",
    "fallbacks": ["google/gemini-2.0-flash-exp"]
  }
}
```

**Вариант 3**: Меньшая модель (qwen2.5:3b вместо 7b)
```bash
ollama pull qwen2.5:3b
ollama create qwen-small:latest -f Modelfile
```

## Безопасность

### Ollama настройки
- Ollama слушает только на `127.0.0.1:11434` (localhost)
- Нет внешнего доступа
- Нет аутентификации (т.к. локальный доступ)

### Рекомендации
- ✅ Не открывать порт 11434 в firewall
- ✅ Регулярно обновлять: `curl -fsSL https://ollama.com/install.sh | sh`
- ✅ Мониторить использование ресурсов

## Откат (если что-то пойдет не так)

### Вернуться на Gemini
```bash
# Остановить Ollama
systemctl stop ollama

# Обновить openclaw.json
# Установить primary = "google/gemini-2.0-flash-exp"

# Перезапустить OpenClaw
systemctl restart openclaw-gateway
```

### Восстановить конфиг
```bash
cp /root/.openclaw/openclaw.json.backup /root/.openclaw/openclaw.json
systemctl restart openclaw-gateway
```

## Чек-лист развертывания

- [ ] Установить Ollama
- [ ] Скачать qwen2.5:7b-instruct
- [ ] Создать qwen-optimized:latest с параметрами
- [ ] Обновить auth profiles в openclaw.json
- [ ] Обновить model config (primary + fallback)
- [ ] Изменить maxConcurrent на 3
- [ ] Перезапустить openclaw-gateway
- [ ] Протестировать ответы от Ollama
- [ ] Протестировать fallback на Gemini
- [ ] Мониторить производительность первые 24 часа
- [ ] Оптимизировать если нужно

## Итоговая конфигурация

**Ожидаемый результат:**
- ✅ Локальная модель Ollama для приватности
- ✅ Fallback на Gemini при проблемах
- ✅ Автоматическое управление ресурсами (compaction mode)
- ✅ Оптимальная производительность для 4-ядерного CPU

**Время развертывания:** ~30 минут
**Сложность:** Средняя
**Риски:** Низкие (есть fallback на Gemini)
