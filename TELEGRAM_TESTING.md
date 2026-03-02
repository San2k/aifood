# 📱 OpenClaw Telegram Testing - AiFood Label Recognition

**Date:** 2026-03-01
**Server:** 199.247.30.52
**Status:** 🟢 READY FOR TESTING

---

## ✅ Pre-flight Checklist

- [x] Agent API running on port 8000
- [x] OCR Service running on port 8001
- [x] PostgreSQL running on port 5433
- [x] Redis running on port 6379
- [x] OpenClaw plugin updated with base64 support
- [x] Plugin synced to `/root/.openclaw/extensions/aifood/dist/`

---

## 🚀 Quick Start (Server Setup)

### 1. Restart OpenClaw

```bash
# SSH to server
ssh root@199.247.30.52

# If using systemd
systemctl restart openclaw
systemctl status openclaw

# OR if running manually
pkill openclaw
nohup openclaw > /var/log/openclaw.log 2>&1 &

# Verify plugin loaded
openclaw plugins list | grep aifood
```

**Expected output:**
```
AiFood | aifood | loaded | global:aifood/dist/index.js | 1.0.0
Plugin registered with 5 tools and /aifood command
```

---

## 📸 Testing Steps

### Step 1: Open Telegram

Open your Telegram app and find the OpenClaw bot.

### Step 2: Send a Photo

Send a photo of a **Russian nutrition label**. Make sure:
- ✅ Label is in focus
- ✅ Good lighting
- ✅ Nutrition table is visible
- ✅ Text is readable

### Step 3: Wait for Response (3-5 seconds)

You should receive:

```
📊 Распознан продукт:

**HIGH-PRO ВИШНЯ-ПЛОМБИР**
Бренд: EXPONENTA

КБЖУ на 100г:
🔥 39 ккал
🥩 Белок: 8г
🍞 Углеводы: 2г
🧈 Жиры: 0г

📝 Метод: Vision AI

✅ Для подтверждения напишите: "подтвердить 150г завтрак"
❌ Для отмены: "отменить"
```

### Step 4: Confirm Consumption

Reply with one of:
- `подтвердить 150г` - Log 150g without meal type
- `подтвердить 150г завтрак` - Log 150g for breakfast
- `подтвердить 200г обед` - Log 200g for lunch
- `отменить` - Cancel scan

**Expected response:**
```
✅ Записано: HIGH-PRO ВИШНЯ-ПЛОМБИР (150.0г)
```

### Step 5: Verify in Database

```bash
# On server
ssh root@199.247.30.52
docker exec -it aifood-postgres psql -U aifood -d aifood -c "SELECT * FROM food_log_entry ORDER BY id DESC LIMIT 1;"
```

---

## 🧪 Test Scenarios

### Scenario 1: Clear Label (Expected: OCR Success)
- **Photo**: High-quality, well-lit Russian label
- **Expected method**: `paddleocr` (OCR confidence > 75%)
- **Expected time**: ~3-4 seconds

### Scenario 2: Blurry Label (Expected: Vision Fallback)
- **Photo**: Slightly blurry or damaged label
- **Expected method**: `gemini` (OCR confidence < 75%)
- **Expected time**: ~5-7 seconds

### Scenario 3: Non-Label Image (Expected: Graceful Failure)
- **Photo**: Random image (not a label)
- **Expected**: Error message explaining no nutrition data found

---

## 🐛 Troubleshooting

### Problem: No Response from Bot

**Check OpenClaw is running:**
```bash
ps aux | grep openclaw
```

**Check OpenClaw logs:**
```bash
# Location varies, common paths:
tail -f /var/log/openclaw.log
journalctl -u openclaw -f
```

**Restart OpenClaw:**
```bash
systemctl restart openclaw
```

### Problem: "Ошибка обработки этикетки"

**Check agent-api logs:**
```bash
cd /root/aifood
docker compose logs --tail=50 agent-api
```

**Common errors:**
- `Failed to download image` - Fixed! Plugin now uses base64
- `Vision extraction incomplete` - Image is not a valid label
- `OCR extraction failed` - Issue with OCR service

**Check all services:**
```bash
docker compose ps
# All should show "healthy"
```

### Problem: Plugin Not Loaded

**Check plugin files:**
```bash
ls -lh /root/.openclaw/extensions/aifood/dist/
# Should show index.js updated today
```

**Check plugin ownership:**
```bash
ls -la /root/.openclaw/extensions/aifood/
# Should be owned by root:root
```

**Fix ownership if needed:**
```bash
chown -R root:root /root/.openclaw/extensions/aifood/
```

**Reload plugin:**
```bash
systemctl restart openclaw
```

---

## 📊 Service Health Check

```bash
# Agent API
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"agent-api","version":"2.0.0"}

# OCR Service
curl http://localhost:8001/health
# Expected: {"status":"ok"}

# PostgreSQL
docker exec aifood-postgres pg_isready
# Expected: accepting connections

# Redis
docker exec aifood-redis redis-cli ping
# Expected: PONG
```

---

## 🎯 Success Criteria

✅ Photo sent via Telegram
✅ Response received within 10 seconds
✅ Product name extracted correctly
✅ КБЖУ values are reasonable (не hallucinated)
✅ Confirmation message works
✅ Entry appears in database
✅ Calories calculated correctly (portion * 100g value)

---

## 📝 Test Log Template

```
Date: 2026-03-01
Tester: [Your Name]
Bot: @[bot_username]

Test 1: Clear Russian Label
- Photo: [describe]
- Processing time: [seconds]
- Method used: [OCR/Vision]
- Product recognized: [yes/no]
- КБЖУ extracted: [yes/no]
- Confirmation worked: [yes/no]
- Result: [PASS/FAIL]

Test 2: Blurry Label
- Photo: [describe]
- Processing time: [seconds]
- Method used: [OCR/Vision]
- Product recognized: [yes/no]
- Result: [PASS/FAIL]

Test 3: Non-Label Image
- Photo: [describe]
- Error message received: [yes/no]
- Result: [PASS/FAIL]
```

---

## 🔗 Useful Links

- **Agent API Swagger:** http://199.247.30.52:8000/docs
- **Production Status:** [FINAL_STATUS.md](FINAL_STATUS.md)
- **Plugin Update Log:** [PLUGIN_UPDATE_STATUS.md](PLUGIN_UPDATE_STATUS.md)

---

## 🎉 Ready to Test!

System is fully deployed and ready for production testing via Telegram/WhatsApp.

**Next step:** Restart OpenClaw and send a photo!
