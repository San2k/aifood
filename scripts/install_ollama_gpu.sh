#!/bin/bash
# Скрипт установки Ollama с GPU на новый сервер
# Server: 199.247.7.186 с NVIDIA A40-8Q (8GB VRAM)

set -e

echo "=== Установка Ollama с GPU поддержкой ==="
echo "Server: 199.247.7.186 (4 CPU, 19GB RAM, NVIDIA A40-8Q 8GB)"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Выбор модели (можно задать через переменную окружения)
MODEL_SIZE=${MODEL_SIZE:-"14b"}  # По умолчанию 14b (рекомендуется)

echo -e "${BLUE}Выбрана модель: qwen2.5:${MODEL_SIZE}-instruct${NC}"
echo ""

# Шаг 0: Проверка GPU
echo -e "${YELLOW}[0/7] Checking GPU availability...${NC}"
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}ERROR: nvidia-smi not found. GPU not available!${NC}"
    exit 1
fi

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)

if [ "$GPU_MEM" -lt 7000 ]; then
    echo -e "${RED}ERROR: Not enough GPU memory. Found ${GPU_MEM}MB, need at least 7000MB${NC}"
    exit 1
fi

echo -e "${GREEN}✓ GPU detected and ready${NC}"
echo ""

# Проверка что скрипт запущен на правильном сервере
EXPECTED_RAM="19"
ACTUAL_RAM=$(free -g | awk '/^Mem:/{print $2}')

if [ "$ACTUAL_RAM" != "$EXPECTED_RAM" ]; then
    echo -e "${YELLOW}WARNING: Expected ${EXPECTED_RAM}GB RAM, found ${ACTUAL_RAM}GB${NC}"
    echo "Are you sure you're on the right server? (y/n)"
    read -r confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted"
        exit 1
    fi
fi

# Шаг 1: Установка Ollama
echo -e "${YELLOW}[1/7] Installing Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo "Ollama already installed: $(ollama --version)"
else
    curl -fsSL https://ollama.com/install.sh | sh
    echo -e "${GREEN}✓ Ollama installed${NC}"
fi

# Проверка systemd service
echo -e "${YELLOW}Checking Ollama service...${NC}"
systemctl enable ollama
systemctl start ollama
sleep 3

# Проверка что Ollama видит GPU
echo -e "${YELLOW}Testing GPU detection by Ollama...${NC}"
journalctl -u ollama --since "10 seconds ago" --no-pager | grep -i "gpu\|cuda" || echo "Note: GPU logs may appear later"

systemctl status ollama --no-pager | head -10
echo -e "${GREEN}✓ Ollama service running${NC}"
echo ""

# Шаг 2: Загрузка базовой модели
echo -e "${YELLOW}[2/7] Pulling base model qwen2.5:${MODEL_SIZE}-instruct...${NC}"
if [ "$MODEL_SIZE" == "14b" ]; then
    echo "Downloading ~8GB model, this will take 15-20 minutes..."
    MODEL_NAME="qwen2.5:14b-instruct"
elif [ "$MODEL_SIZE" == "7b" ]; then
    echo "Downloading ~4.7GB model, this will take 10-15 minutes..."
    MODEL_NAME="qwen2.5:7b-instruct"
elif [ "$MODEL_SIZE" == "32b" ]; then
    echo "Downloading ~18GB model (quantized), this will take 25-30 minutes..."
    MODEL_NAME="qwen2.5:32b-instruct-q4_K_M"
else
    echo -e "${RED}Invalid MODEL_SIZE: $MODEL_SIZE. Use 7b, 14b, or 32b${NC}"
    exit 1
fi

ollama pull $MODEL_NAME
echo -e "${GREEN}✓ Base model downloaded${NC}"
echo ""

# Шаг 3: Создание оптимизированной модели для GPU
echo -e "${YELLOW}[3/7] Creating GPU-optimized model...${NC}"

if [ "$MODEL_SIZE" == "32b" ]; then
    NUM_CTX=4096
else
    NUM_CTX=8192
fi

cat > /tmp/Modelfile << EOF
FROM $MODEL_NAME

PARAMETER temperature 0.25
PARAMETER num_ctx $NUM_CTX
PARAMETER num_predict 1024

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

OPTIMIZED_NAME="qwen-${MODEL_SIZE}b-gpu:latest"
ollama create $OPTIMIZED_NAME -f /tmp/Modelfile
echo -e "${GREEN}✓ Optimized model created: $OPTIMIZED_NAME${NC}"
echo ""

# Список моделей
echo "Available models:"
ollama list
echo ""

# Шаг 4: Тест модели с GPU
echo -e "${YELLOW}[4/7] Testing model with GPU...${NC}"
echo "Sending test prompt (this should use GPU)..."
echo ""

# Запуск в фоне чтобы можно было мониторить GPU
ollama run $OPTIMIZED_NAME "Hello! Please respond with exactly one short sentence." &
OLLAMA_PID=$!

# Ждем 2 секунды и проверяем GPU
sleep 2
echo -e "${BLUE}GPU status during inference:${NC}"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

wait $OLLAMA_PID
echo ""
echo -e "${GREEN}✓ Model test completed${NC}"
echo ""

# Финальная проверка GPU usage
echo -e "${BLUE}Final GPU check:${NC}"
nvidia-smi
echo ""

# Шаг 5: Обновление OpenClaw конфигурации
echo -e "${YELLOW}[5/7] Updating OpenClaw configuration...${NC}"

# Бэкап
BACKUP_FILE="/root/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)"
cp /root/.openclaw/openclaw.json $BACKUP_FILE
echo "Backup created: $BACKUP_FILE"

# Обновление конфигурации через jq
PRIMARY_MODEL="ollama/$OPTIMIZED_NAME"

jq --arg primary "$PRIMARY_MODEL" \
   '.auth.profiles."ollama:default" = {"provider": "ollama", "mode": "api_key"} |
    .agents.defaults.model.primary = $primary |
    .agents.defaults.model.fallbacks = ["google/gemini-2.0-flash-exp"] |
    .agents.defaults.models = {($primary): {}, "google/gemini-2.0-flash-exp": {}} |
    .agents.defaults.maxConcurrent = 6' /root/.openclaw/openclaw.json > /tmp/openclaw-new.json

mv /tmp/openclaw-new.json /root/.openclaw/openclaw.json
echo -e "${GREEN}✓ Configuration updated${NC}"
echo ""

# Показать изменения
echo "New model configuration:"
jq '.agents.defaults.model' /root/.openclaw/openclaw.json
echo ""

# Шаг 6: Перезапуск OpenClaw Gateway
echo -e "${YELLOW}[6/7] Restarting OpenClaw Gateway...${NC}"
systemctl restart openclaw-gateway
sleep 5

# Проверка статуса
echo ""
echo "OpenClaw Gateway status:"
systemctl status openclaw-gateway --no-pager | head -15
echo ""

# Логи
echo -e "${YELLOW}Recent gateway logs:${NC}"
journalctl -u openclaw-gateway --since "1 minute ago" --no-pager | tail -20
echo ""

# Шаг 7: Финальная проверка и советы
echo -e "${YELLOW}[7/7] Final verification...${NC}"
echo ""

# Проверка что плагин загружен
echo "Checking AiFood plugin:"
journalctl -u openclaw-gateway --since "2 minutes ago" --no-pager | grep -i "aifood" | tail -5
echo ""

# Финальная проверка GPU
echo -e "${BLUE}Current GPU status:${NC}"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
echo ""

# Финальное сообщение
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo "Configuration Summary:"
echo "  Primary model: $PRIMARY_MODEL"
echo "  Model size: ${MODEL_SIZE}B parameters"
echo "  GPU: NVIDIA A40-8Q (8GB VRAM)"
echo "  Context window: $NUM_CTX tokens"
echo "  Max output: 1024 tokens"
echo "  Temperature: 0.25"
echo "  Max concurrent: 6"
echo "  Fallback: google/gemini-2.0-flash-exp"
echo ""

if [ "$MODEL_SIZE" == "14b" ]; then
    echo "Expected performance:"
    echo "  Speed: 100-200 tokens/sec"
    echo "  Response time: 3-7 seconds"
    echo "  Quality: Excellent ⭐⭐⭐⭐⭐"
elif [ "$MODEL_SIZE" == "7b" ]; then
    echo "Expected performance:"
    echo "  Speed: 200-400 tokens/sec"
    echo "  Response time: 2-5 seconds"
    echo "  Quality: Good ⭐⭐⭐⭐"
elif [ "$MODEL_SIZE" == "32b" ]; then
    echo "Expected performance:"
    echo "  Speed: 50-100 tokens/sec"
    echo "  Response time: 5-10 seconds"
    echo "  Quality: Exceptional ⭐⭐⭐⭐⭐"
fi
echo ""

echo "Next steps:"
echo "  1. Send a test message to Telegram bot @LenoxAI_bot"
echo "  2. Monitor GPU usage: watch -n 1 nvidia-smi"
echo "  3. Monitor logs: journalctl -u openclaw-gateway -f"
echo "  4. Monitor Ollama: journalctl -u ollama -f"
echo ""
echo "Monitoring commands:"
echo "  GPU usage:     nvidia-smi"
echo "  GPU realtime:  watch -n 1 nvidia-smi"
echo "  GPU detailed:  nvidia-smi dmon -s pucvmet"
echo "  Temperature:   nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader"
echo "  Gateway logs:  journalctl -u openclaw-gateway -f"
echo "  Ollama logs:   journalctl -u ollama -f"
echo ""
echo "If performance is not as expected:"
echo "  1. Check GPU usage: watch -n 1 nvidia-smi"
echo "  2. GPU-Util should be 80-100% during inference"
echo "  3. If GPU-Util is 0%, Ollama is not using GPU"
echo "  4. Check Ollama logs: journalctl -u ollama -f"
echo ""
echo "To revert to Gemini-only:"
echo "  cp $BACKUP_FILE /root/.openclaw/openclaw.json"
echo "  systemctl restart openclaw-gateway"
echo ""
echo "To switch models:"
echo "  MODEL_SIZE=7b  bash $0  # Faster, smaller"
echo "  MODEL_SIZE=14b bash $0  # Recommended (current)"
echo "  MODEL_SIZE=32b bash $0  # Best quality"
echo ""
