# План развертывания Ollama на новом сервере (с GPU!)

## 🚀 ВАЖНО: На новом сервере есть GPU!

**NVIDIA A40-8Q с 8GB VRAM** - профессиональная GPU для дата-центров!

Это значительно улучшает возможности по сравнению со старым сервером.

## Сравнение серверов

| Характеристика | Старый (199.247.30.52) | Новый (199.247.7.186) |
|----------------|------------------------|----------------------|
| CPU | 6 ядер (Xeon Skylake) | 4 ядра (Core Broadwell) |
| RAM | 15GB (доступно 13GB) | 19GB (доступно 18GB) |
| **GPU** | ❌ **Нет** | ✅ **NVIDIA A40-8Q (8GB)** |
| Swap | 8GB | 8GB |
| Disk | - | 338GB (306GB free) |
| Текущая модель | qwen-optimized (CPU) | google/gemini-2.0-flash-exp |
| Inference speed | 10-20 tokens/sec (CPU) | **200-400 tokens/sec (GPU!)** |

## Текущая конфигурация на старом сервере

### Модель (CPU inference)
- **Primary**: `ollama/qwen-optimized:latest` (локальная, на CPU)
- **Fallback**: `google/gemini-2.0-flash-exp` (облачная)
- **Size**: 4.7 GB
- **Base model**: qwen2.5:7b-instruct

### Параметры Modelfile (ограничены CPU)
```
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.25
PARAMETER num_ctx 4096        # Ограничено для CPU
PARAMETER num_predict 512     # Ограничено для CPU
```

### OpenClaw настройки (CPU)
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

## 🎯 НОВАЯ конфигурация для GPU сервера

### Преимущества GPU
✅ **10-20x быстрее** inference (200-400 tokens/sec vs 10-20)
✅ **Больший контекст** можно использовать (8192 vs 4096)
✅ **Больше параллельных запросов** (6-8 vs 3-4)
✅ **Можно использовать бОльшие модели** (до 13B с quantization)
✅ **Мгновенные ответы** (2-5 секунд vs 20-50 секунд)

### Рекомендуемые модели для A40 8GB

#### Вариант 1: qwen2.5:7b (как на старом сервере, но на GPU)
```bash
# Та же модель, но в 10-20 раз быстрее
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.25
PARAMETER num_ctx 8192         # Увеличено с 4096
PARAMETER num_predict 1024     # Увеличено с 512
```
- **Size**: 4.7 GB VRAM
- **Speed**: 200-400 tokens/sec
- **Context**: 8192 tokens

#### Вариант 2: qwen2.5:14b (больше, умнее, всё ещё быстро) ⭐ РЕКОМЕНДУЕТСЯ
```bash
FROM qwen2.5:14b-instruct
PARAMETER temperature 0.25
PARAMETER num_ctx 8192
PARAMETER num_predict 1024
```
- **Size**: ~7.5 GB VRAM (помещается в 8GB)
- **Speed**: 100-200 tokens/sec
- **Context**: 8192 tokens
- **Quality**: Заметно лучше чем 7b

#### Вариант 3: qwen2.5:32b-instruct-q4_K_M (самый умный, квантованный)
```bash
FROM qwen2.5:32b-instruct-q4_K_M
PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 1024
```
- **Size**: ~7.8 GB VRAM
- **Speed**: 50-100 tokens/sec
- **Quality**: Максимальная

### Оптимальная конфигурация OpenClaw (GPU)

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
        "primary": "ollama/qwen-14b-gpu:latest",
        "fallbacks": ["google/gemini-2.0-flash-exp"]
      },
      "models": {
        "ollama/qwen-14b-gpu:latest": {},
        "google/gemini-2.0-flash-exp": {}
      },
      "workspace": "/root/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 6
    }
  }
}
```

**Изменения для GPU:**
- ✅ `maxConcurrent: 6` (было 3 для CPU) - GPU справляется
- ✅ Модель: qwen2.5:14b вместо 7b (больше качество)
- ✅ num_ctx: 8192 (было 4096)
- ✅ num_predict: 1024 (было 512)

### auth.json
```json
{
  "google": {
    "type": "api_key",
    "key": "YOUR_GOOGLE_AI_API_KEY"
  }
}
```

## Этапы развертывания (GPU версия)

### Шаг 0: Проверка GPU (1 минута)
```bash
# Проверить что GPU доступна
nvidia-smi

# Должно показать:
# NVIDIA A40-8Q, 8192 MiB VRAM
```

### Шаг 1: Установка Ollama (5 минут)
```bash
# Установка (автоматически обнаружит GPU)
curl -fsSL https://ollama.com/install.sh | sh

# Проверка
systemctl status ollama
ollama --version
```

### Шаг 2: Загрузка модели (15-20 минут)
```bash
# ВАРИАНТ 1: Та же модель что на старом сервере (быстро)
ollama pull qwen2.5:7b-instruct

# ВАРИАНТ 2: Более умная модель (рекомендуется) ⭐
ollama pull qwen2.5:14b-instruct

# ВАРИАНТ 3: Максимальное качество
ollama pull qwen2.5:32b-instruct-q4_K_M

# Проверка
ollama list
```

### Шаг 3: Создание оптимизированной модели (1 минута)

#### Для qwen2.5:7b (как на старом):
```bash
cat > /tmp/Modelfile << 'EOF'
FROM qwen2.5:7b-instruct

PARAMETER temperature 0.25
PARAMETER num_ctx 8192
PARAMETER num_predict 1024

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

ollama create qwen-gpu:latest -f /tmp/Modelfile
```

#### Для qwen2.5:14b (рекомендуется) ⭐:
```bash
cat > /tmp/Modelfile << 'EOF'
FROM qwen2.5:14b-instruct

PARAMETER temperature 0.25
PARAMETER num_ctx 8192
PARAMETER num_predict 1024

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

ollama create qwen-14b-gpu:latest -f /tmp/Modelfile
```

### Шаг 4: Тест с GPU (2 минуты)
```bash
# Запустить модель и проверить использование GPU
ollama run qwen-14b-gpu:latest "Привет! Напиши короткий ответ."

# В другом терминале смотреть GPU usage
watch -n 1 nvidia-smi

# Должно показать:
# GPU-Util: 80-100% во время inference
# Memory-Usage: ~7000-7500 MiB / 8192 MiB
```

### Шаг 5: Обновление OpenClaw конфигурации (2 минуты)
```bash
# Бэкап текущего конфига
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.backup

# Обновить openclaw.json через jq
jq '.auth.profiles."ollama:default" = {"provider": "ollama", "mode": "api_key"} |
    .agents.defaults.model.primary = "ollama/qwen-14b-gpu:latest" |
    .agents.defaults.model.fallbacks = ["google/gemini-2.0-flash-exp"] |
    .agents.defaults.models = {"ollama/qwen-14b-gpu:latest": {}, "google/gemini-2.0-flash-exp": {}} |
    .agents.defaults.maxConcurrent = 6' /root/.openclaw/openclaw.json > /tmp/openclaw-new.json

mv /tmp/openclaw-new.json /root/.openclaw/openclaw.json

# Проверка
jq '.agents.defaults.model' /root/.openclaw/openclaw.json
```

### Шаг 6: Перезапуск OpenClaw (1 минута)
```bash
systemctl restart openclaw-gateway
sleep 5
systemctl status openclaw-gateway
journalctl -u openclaw-gateway -f
```

### Шаг 7: Тестирование (5 минут)
```bash
# Отправить сообщение в Telegram бот
# Проверить:
# 1. Ответ приходит от ollama/qwen-14b-gpu
# 2. Скорость ~2-5 секунд (было 20-50 на CPU!)
# 3. Качество ответов высокое

# Мониторить GPU
watch -n 1 nvidia-smi

# Логи
journalctl -u ollama -f
journalctl -u openclaw-gateway -f
```

## Ожидаемая производительность

### Старый сервер (6 CPU, без GPU)
- Первый токен: ~5-10 секунд
- Генерация: ~10-20 токенов/сек
- Общее время ответа: **15-40 секунд**
- Качество: хорошее (qwen2.5:7b)

### Новый сервер (4 CPU + NVIDIA A40 8GB)

#### С qwen2.5:7b-instruct на GPU:
- Первый токен: ~0.5-1 секунда
- Генерация: ~200-400 токенов/сек
- Общее время ответа: **2-5 секунд** ⚡
- Качество: хорошее (та же модель)
- **Ускорение: 5-10x**

#### С qwen2.5:14b-instruct на GPU (рекомендуется):
- Первый токен: ~0.8-1.5 секунды
- Генерация: ~100-200 токенов/сек
- Общее время ответа: **3-7 секунд** ⚡
- Качество: **отличное** (лучше чем 7b)
- **Ускорение: 4-8x + выше качество**

#### С qwen2.5:32b-instruct-q4_K_M на GPU:
- Первый токен: ~1-2 секунды
- Генерация: ~50-100 токенов/сек
- Общее время ответа: **5-10 секунд**
- Качество: **превосходное** (максимум)
- **Ускорение: 3-5x + максимальное качество**

## Мониторинг GPU

### Команды для мониторинга
```bash
# GPU статус в реальном времени
watch -n 1 nvidia-smi

# GPU использование (детально)
nvidia-smi dmon -s pucvmet

# GPU temperature
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader

# GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Ollama процессы на GPU
nvidia-smi pmon

# Ollama логи
journalctl -u ollama -f

# OpenClaw логи
journalctl -u openclaw-gateway -f

# Комплексный мониторинг
htop & watch -n 1 nvidia-smi
```

### Признаки правильной работы
- ✅ `nvidia-smi` показывает Ollama процесс
- ✅ GPU-Util: 80-100% во время inference
- ✅ Memory-Usage: ~4-8 GB (зависит от модели)
- ✅ Temperature: 40-80°C (нормально)
- ✅ Ответы приходят за 2-7 секунд

### Признаки проблем
- ❌ GPU-Util: 0% → модель не использует GPU (проверить установку)
- ❌ Memory-Usage: > 7500 MB → модель слишком большая
- ❌ Temperature: > 85°C → проблемы с охлаждением
- ❌ Ответы > 15 секунд → что-то не так, проверить логи

## Сравнение с облачными API

| Провайдер | Скорость | Стоимость | Приватность | Качество |
|-----------|----------|-----------|-------------|----------|
| **Ollama GPU** | ⚡⚡⚡⚡⚡ 2-5 сек | 💰 FREE | 🔒 100% | ⭐⭐⭐⭐⭐ |
| Gemini Flash | ⚡⚡⚡⚡ 1-3 сек | 💰 FREE tier | ❌ Облако | ⭐⭐⭐⭐ |
| Groq | ⚡⚡⚡⚡⚡ 0.5-2 сек | 💰 FREE tier | ❌ Облако | ⭐⭐⭐⭐ |
| Ollama CPU | ⚡ 15-40 сек | 💰 FREE | 🔒 100% | ⭐⭐⭐⭐ |

**Вывод**: С GPU Ollama становится конкурентоспособным по скорости с облачными API, но с полной приватностью!

## Альтернативные варианты

### Если нужна максимальная скорость:
```json
{
  "model": {
    "primary": "groq/llama-3.1-70b-versatile",
    "fallbacks": ["ollama/qwen-14b-gpu:latest"]
  }
}
```
Groq (облако) для скорости, Ollama (локально) для приватности.

### Если нужна максимальная приватность:
```json
{
  "model": {
    "primary": "ollama/qwen-14b-gpu:latest"
  }
}
```
Только локальная модель, без fallback.

### Если нужно максимальное качество:
```bash
# Установить qwen2.5:32b
ollama pull qwen2.5:32b-instruct-q4_K_M
ollama create qwen-32b-gpu:latest -f Modelfile
```

## Безопасность

### Ollama + GPU настройки
- Ollama слушает только на `127.0.0.1:11434` (localhost)
- GPU доступна только локальным процессам
- Нет внешнего доступа к GPU или Ollama
- CUDA drivers безопасны (обновляются через apt)

### Рекомендации
- ✅ Не открывать порт 11434 в firewall
- ✅ Регулярно обновлять драйверы: `apt update && apt upgrade`
- ✅ Мониторить температуру GPU
- ✅ Ограничить VRAM если нужно: `OLLAMA_GPU_LAYERS=32`

## Откат (если что-то пойдет не так)

### Вернуться на Gemini
```bash
# Остановить Ollama
systemctl stop ollama

# Обновить openclaw.json
jq '.agents.defaults.model.primary = "google/gemini-2.0-flash-exp"' \
  /root/.openclaw/openclaw.json > /tmp/openclaw-new.json
mv /tmp/openclaw-new.json /root/.openclaw/openclaw.json

# Перезапустить OpenClaw
systemctl restart openclaw-gateway
```

### Восстановить конфиг
```bash
cp /root/.openclaw/openclaw.json.backup /root/.openclaw/openclaw.json
systemctl restart openclaw-gateway
```

### Уменьшить модель если не хватает VRAM
```bash
# Если 14b не помещается, вернуться на 7b
ollama create qwen-7b-gpu:latest -f Modelfile-7b
# Обновить primary model в конфиге
```

## Автоматический скрипт установки

Скрипт: `scripts/install_ollama_gpu.sh`

```bash
# На новом сервере
cd /opt/aifood
bash scripts/install_ollama_gpu.sh
```

Скрипт автоматически:
1. Проверяет наличие GPU
2. Устанавливает Ollama
3. Скачивает модель (по умолчанию qwen2.5:14b)
4. Создает оптимизированную версию с GPU параметрами
5. Обновляет OpenClaw конфигурацию
6. Тестирует GPU inference
7. Перезапускает сервисы

## Чек-лист развертывания

- [ ] Проверить GPU: `nvidia-smi`
- [ ] Установить Ollama
- [ ] Выбрать модель (7b, 14b, или 32b)
- [ ] Скачать модель: `ollama pull qwen2.5:14b-instruct`
- [ ] Создать оптимизированную версию с GPU параметрами
- [ ] Протестировать GPU usage: `nvidia-smi` во время inference
- [ ] Обновить OpenClaw auth profiles
- [ ] Обновить model config (primary + fallback)
- [ ] Изменить maxConcurrent на 6
- [ ] Перезапустить openclaw-gateway
- [ ] Протестировать скорость ответов (должно быть 2-7 сек)
- [ ] Протестировать fallback на Gemini
- [ ] Мониторить GPU температуру первые 24 часа
- [ ] Оптимизировать если нужно

## Итоговая конфигурация

**Рекомендуемая конфигурация:**
- ✅ Модель: qwen2.5:14b-instruct на GPU (отличное качество)
- ✅ Fallback: Gemini Flash (на случай проблем)
- ✅ Context: 8192 tokens (в 2 раза больше чем на CPU)
- ✅ Max concurrent: 6 (в 2 раза больше чем на CPU)
- ✅ Скорость: 3-7 секунд (в 5-8 раз быстрее чем на CPU)
- ✅ Приватность: 100% локальная обработка
- ✅ Стоимость: $0

**Время развертывания:** ~30 минут
**Сложность:** Средняя
**Риски:** Низкие (есть fallback на Gemini)
**Выигрыш:** Огромный! GPU даёт 5-10x ускорение + можно использовать большие модели
