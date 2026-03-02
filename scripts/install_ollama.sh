#!/bin/bash
# Скрипт установки Ollama на новый сервер с настройками из старого

set -e

echo "=== Установка Ollama на новый сервер ==="
echo "Server: 199.247.7.186 (4 CPU, 19GB RAM)"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка что скрипт запущен на правильном сервере
EXPECTED_RAM="19"
ACTUAL_RAM=$(free -g | awk '/^Mem:/{print $2}')

if [ "$ACTUAL_RAM" != "$EXPECTED_RAM" ]; then
    echo -e "${RED}WARNING: Expected ${EXPECTED_RAM}GB RAM, found ${ACTUAL_RAM}GB${NC}"
    echo "Are you sure you're on the right server? (y/n)"
    read -r confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted"
        exit 1
    fi
fi

# Шаг 1: Установка Ollama
echo -e "${YELLOW}[1/6] Installing Ollama...${NC}"
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
systemctl status ollama --no-pager | head -10

# Шаг 2: Загрузка базовой модели
echo ""
echo -e "${YELLOW}[2/6] Pulling base model qwen2.5:7b-instruct (~4.7GB)...${NC}"
echo "This will take 10-15 minutes depending on network speed"
ollama pull qwen2.5:7b-instruct
echo -e "${GREEN}✓ Base model downloaded${NC}"

# Шаг 3: Создание оптимизированной модели
echo ""
echo -e "${YELLOW}[3/6] Creating optimized model...${NC}"
cat > /tmp/Modelfile << 'EOF'
FROM qwen2.5:7b-instruct

PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 512

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

ollama create qwen-optimized:latest -f /tmp/Modelfile
echo -e "${GREEN}✓ Optimized model created${NC}"

# Список моделей
echo ""
echo "Available models:"
ollama list

# Шаг 4: Тест модели
echo ""
echo -e "${YELLOW}[4/6] Testing model...${NC}"
echo "Sending test prompt..."
ollama run qwen-optimized:latest "Hello! Please respond in one sentence." --verbose
echo -e "${GREEN}✓ Model test completed${NC}"

# Шаг 5: Обновление OpenClaw конфигурации
echo ""
echo -e "${YELLOW}[5/6] Updating OpenClaw configuration...${NC}"

# Бэкап
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)
echo "Backup created: /root/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)"

# Обновление конфигурации через jq
jq '.auth.profiles."ollama:default" = {"provider": "ollama", "mode": "api_key"} |
    .agents.defaults.model.primary = "ollama/qwen-optimized:latest" |
    .agents.defaults.model.fallbacks = ["google/gemini-2.0-flash-exp"] |
    .agents.defaults.models = {"ollama/qwen-optimized:latest": {}, "google/gemini-2.0-flash-exp": {}} |
    .agents.defaults.maxConcurrent = 3' /root/.openclaw/openclaw.json > /tmp/openclaw-new.json

mv /tmp/openclaw-new.json /root/.openclaw/openclaw.json
echo -e "${GREEN}✓ Configuration updated${NC}"

# Показать изменения
echo ""
echo "New model configuration:"
jq '.agents.defaults.model' /root/.openclaw/openclaw.json

# Шаг 6: Перезапуск OpenClaw Gateway
echo ""
echo -e "${YELLOW}[6/6] Restarting OpenClaw Gateway...${NC}"
systemctl restart openclaw-gateway
sleep 5

# Проверка статуса
echo ""
echo "OpenClaw Gateway status:"
systemctl status openclaw-gateway --no-pager | head -15

# Логи
echo ""
echo -e "${YELLOW}Recent logs:${NC}"
journalctl -u openclaw-gateway --since "1 minute ago" --no-pager | tail -20

# Финальная проверка
echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "Configuration:"
echo "  Primary model: ollama/qwen-optimized:latest (local)"
echo "  Fallback: google/gemini-2.0-flash-exp (cloud)"
echo "  Max concurrent: 3"
echo "  Compaction: safeguard"
echo ""
echo "Model specs:"
echo "  Size: 4.7GB"
echo "  Context: 4096 tokens"
echo "  Max output: 512 tokens"
echo "  Temperature: 0.25"
echo ""
echo "Next steps:"
echo "  1. Send a test message to Telegram bot @LenoxAI_bot"
echo "  2. Monitor logs: journalctl -u openclaw-gateway -f"
echo "  3. Monitor Ollama: journalctl -u ollama -f"
echo "  4. Check resources: htop"
echo ""
echo "If Ollama is too slow, revert to Gemini:"
echo "  cp /root/.openclaw/openclaw.json.backup-* /root/.openclaw/openclaw.json"
echo "  systemctl restart openclaw-gateway"
echo ""
