# Ollama Setup Guide for Mac M1 Max

Your nutrition bot now uses **Ollama** for free, unlimited AI processing on your Mac!

## ✅ What You Get

- **Free & Unlimited:** No API costs
- **Fast:** 2-4 seconds per request on M1 Max
- **Private:** All data stays on your machine
- **Fallback:** Automatically uses OpenAI if Ollama fails

## 🚀 Installation Steps

### Step 1: Install Ollama on Your Mac

```bash
# Option A: Download from website (recommended)
# Visit: https://ollama.com/download
# Click "Download for macOS" and install the app

# Option B: Install via Homebrew
brew install ollama
```

### Step 2: Start Ollama Service

```bash
# Start Ollama (it will run in the background)
ollama serve
```

**Note:** On Mac, Ollama runs as a menu bar app. Just click the Ollama icon in your menu bar to verify it's running.

### Step 3: Download AI Models

Open a new terminal window and run:

```bash
# For text parsing (food extraction)
ollama pull mistral

# For vision (product recognition from photos)
ollama pull llava:13b
```

**Download sizes:**
- Mistral: ~4.1GB
- LLaVA 13B: ~7.4GB

This will take 10-30 minutes depending on your internet speed.

### Step 4: Verify Installation

```bash
# Test Mistral
ollama run mistral "Hello, extract food items from: 2 eggs and 100g rice"

# Test LLaVA vision
ollama run llava:13b "What do you see in this image?"
```

If both work, you're all set!

## 🔧 Configuration

Your bot is already configured to use Ollama. Check [.env](/.env):

```bash
# Current configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_TEXT=mistral
OLLAMA_MODEL_VISION=llava:13b
```

## ⚙️ Switching Between Providers

### Use Ollama (default):
```bash
# In .env file
LLM_PROVIDER=ollama
```

### Switch back to OpenAI:
```bash
# In .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

Then restart:
```bash
docker-compose restart agent-api
```

## 📊 Performance on M1 Max

**Expected speeds:**
- Text parsing (Mistral): ~1 second
- Vision recognition (LLaVA 13B): 2-4 seconds per image
- Nutrition advice: ~1 second

**Resource usage:**
- RAM: ~8-12GB (including model + processing)
- CPU: Low (handled by Neural Engine)
- GPU: Metal acceleration (efficient)

## 🧪 Testing

Try these in your Telegram bot:

```
# Text input
съел 2 яйца и 100г риса

# Should work instantly with Mistral
```

```
# Photo input
[Send a photo of a food package]

# Should recognize product in 2-4 seconds
```

## 🐛 Troubleshooting

### Ollama not connecting

Check if Ollama is running:
```bash
# Should return model list
curl http://localhost:11434/api/tags
```

If not running:
```bash
# Start Ollama
ollama serve
```

### Slow performance

**If vision is slow (>10 seconds):**
- Try smaller model: `ollama pull llava` (7B version)
- Update .env: `OLLAMA_MODEL_VISION=llava`
- Restart: `docker-compose restart agent-api`

**Check Ollama status:**
```bash
# See what models are loaded
ps aux | grep ollama

# Check memory usage
Activity Monitor → Search "Ollama"
```

### Docker can't reach Ollama

Verify host connection:
```bash
# From inside Docker container
docker exec -it nutrition_agent_api curl http://host.docker.internal:11434/api/tags
```

Should return JSON with model list.

### Model not found

Download models again:
```bash
ollama pull mistral
ollama pull llava:13b
```

### Falling back to OpenAI

Check logs:
```bash
docker-compose logs agent-api | grep -i "ollama"
```

Look for connection errors or timeout messages.

## 📈 Advanced: Using Faster Models

If you want even faster responses, try these alternatives:

### For text (faster than Mistral):
```bash
ollama pull phi3
```
Update .env:
```
OLLAMA_MODEL_TEXT=phi3
```

### For vision (faster than LLaVA 13B):
```bash
ollama pull llava  # 7B version
```
Update .env:
```
OLLAMA_MODEL_VISION=llava
```

Restart:
```bash
docker-compose restart agent-api
```

## 🔄 Updating Models

```bash
# Update to latest version
ollama pull mistral
ollama pull llava:13b

# Remove old versions to save space
ollama rm old-model-name
```

## 💾 Disk Space Management

Models location: `~/.ollama/models`

```bash
# Check model sizes
du -h ~/.ollama/models

# Remove unused models
ollama list
ollama rm model-name
```

## ✨ Next Steps

1. Install Ollama
2. Download models
3. Test the bot
4. Enjoy unlimited free AI!

**Need help?** Check the logs:
```bash
# Ollama logs
ollama logs

# Bot logs
docker-compose logs -f agent-api
```

---

**Ollama is now your default AI provider!** 🎉

The bot will automatically fall back to OpenAI if Ollama is unavailable, so there's no risk of downtime.
