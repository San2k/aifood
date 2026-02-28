# Testing Guide - AI Nutrition Bot

This document provides comprehensive testing scenarios for the AI Nutrition Bot MVP.

## Prerequisites

Before testing, ensure:
1. All services are running (`./scripts/startup.sh`)
2. Database migrations completed successfully
3. All API keys are configured in `.env`:
   - `TELEGRAM_BOT_TOKEN` - Valid bot token from @BotFather
   - `OPENAI_API_KEY` - Valid OpenAI API key with GPT-4 access
   - `FATSECRET_CLIENT_ID` - FatSecret API client ID
   - `FATSECRET_CLIENT_SECRET` - FatSecret API client secret

## Service Health Checks

### 1. Check All Services Are Running

```bash
docker-compose ps
```

Expected output: All services should be "Up"
- postgres
- redis
- agent-api
- telegram-bot

### 2. Verify Agent API Health

```bash
curl http://localhost:8000/v1/health
```

Expected: `{"status":"healthy","service":"agent-api"}`

### 3. Check Database Connection

```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c "\dt"
```

Expected: List of tables including:
- user_profile
- food_log_entry
- conversation_state
- label_scan
- daily_summary

### 4. Check Bot Logs

```bash
docker-compose logs -f telegram-bot
```

Expected: "Bot started. Polling for updates..."

## Test Scenarios

### Scenario 1: User Registration

**Objective**: Verify new user creation

1. Open Telegram and find your bot
2. Send: `/start`

**Expected Results**:
- Bot responds with welcome message
- Message includes:
  - User's first name in greeting
  - Instructions on how to use the bot
  - List of available commands

**Database Verification**:
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT id, telegram_id, username, first_name FROM user_profile ORDER BY created_at DESC LIMIT 1;"
```

Expected: New user record with your telegram_id

**Logs to Check**:
```bash
docker-compose logs agent-api | grep "Created new user"
```

---

### Scenario 2: Simple Text Input (Single Food)

**Objective**: Test basic food logging

1. Send: `Съел 2 яйца`

**Expected Flow**:
1. Bot processes message
2. May ask clarification: "Сколько грамм?" (How many grams?)
3. Respond: `100г` or `100`
4. Bot searches FatSecret
5. If single match found → auto-selects
6. Bot saves entry and shows totals

**Expected Final Response**:
```
✅ Сохранено!

📊 Итого за сегодня:
Калории: ~140 ккал
Белки: ~12г
Углеводы: ~1г
Жиры: ~10г
```

**Database Verification**:
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT food_name, calories, protein FROM food_log_entry ORDER BY created_at DESC LIMIT 1;"
```

**Logs to Check**:
```bash
# Check parsing
docker-compose logs agent-api | grep "normalize_input"

# Check FatSecret search
docker-compose logs agent-api | grep "fatsecret_search"

# Check entry saved
docker-compose logs agent-api | grep "Saved food entry"
```

---

### Scenario 3: Multiple Foods in One Message

**Objective**: Test parsing multiple food items

1. Send: `Съел 2 яйца и 150г гречки`

**Expected Flow**:
1. Bot parses two items: "яйца" and "гречка"
2. May ask clarifications:
   - Weight for eggs?
   - Is buckwheat dry or cooked?
3. Respond to each clarification
4. Bot processes each food separately
5. Saves both entries
6. Shows combined totals

**Expected Final Response**:
```
✅ Сохранено!

📊 Итого за сегодня:
Калории: ~300-400 ккал
...
```

**Database Verification**:
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT food_name, calories FROM food_log_entry WHERE consumed_at::date = CURRENT_DATE ORDER BY created_at DESC LIMIT 5;"
```

---

### Scenario 4: Clarification with Inline Keyboard

**Objective**: Test inline button interactions

1. Send: `Съел гречку`

**Expected Flow**:
1. Bot asks: "Сколько грамм гречки?"
2. Inline keyboard appears with options (if implemented)
3. OR bot waits for text response
4. Click button or type: `150`
5. Bot asks: "Гречка сухая или варёная?"
6. Inline keyboard with options:
   - Сухая
   - Варёная
7. Select "Варёная"
8. Bot searches and saves

**Expected Behavior**:
- Buttons should be clickable
- Callback should be processed
- Previous message keyboard should disappear after selection
- Final response with totals

**Logs to Check**:
```bash
docker-compose logs telegram-bot | grep "Clarification callback"
```

---

### Scenario 5: Multiple FatSecret Matches

**Objective**: Test food selection from multiple results

1. Send: `Съел курицу 200г`

**Expected Flow**:
1. Bot searches FatSecret for "курица"
2. Multiple results found:
   - Chicken breast, cooked
   - Chicken thigh, cooked
   - Chicken, raw
   - etc.
3. Bot shows inline keyboard with top 5 matches
4. Select desired option
5. Bot gets servings and calculates nutrition
6. Saves entry

**Expected Response**:
Inline keyboard with food options

**Logs to Check**:
```bash
docker-compose logs agent-api | grep "Multiple food candidates"
```

---

### Scenario 6: Daily Report

**Objective**: Test /today command with real data

**Prerequisites**: Have at least 1 food entry logged today

1. Send: `/today`

**Expected Response**:
```
📊 **Отчёт за сегодня**

🔥 Калории: XXX ккал
🥩 Белки: XXг
🍞 Углеводы: XXг
🥑 Жиры: XXг

📝 **Записей:** N
```

**If no entries**:
```
📊 **Отчёт за сегодня**
...
Калории: 0 ккал
...
📝 **Записей:** 0

💡 Пока нет записей за сегодня. Начните логировать!
```

**API Call Verification**:
```bash
# Replace TELEGRAM_ID with your actual telegram ID
curl http://localhost:8000/v1/reports/today/YOUR_TELEGRAM_ID
```

---

### Scenario 7: Weekly Report

**Objective**: Test /week command

**Prerequisites**: Have entries across multiple days (ideally)

1. Send: `/week`

**Expected Response**:
```
📊 **Отчёт за неделю**

Калории за последние 7 дней:

📅 Пн (DD.MM): XXX ккал
📅 Вт (DD.MM): XXX ккал
...
📅 Вс (DD.MM): XXX ккал

📈 **Среднее:** XXX ккал/день
```

**API Call Verification**:
```bash
curl http://localhost:8000/v1/reports/week/YOUR_TELEGRAM_ID
```

---

### Scenario 8: Help Command

**Objective**: Verify help documentation

1. Send: `/help`

**Expected Response**:
- List of all commands
- Instructions for logging food
- Examples
- Information about data sources (FatSecret)

---

### Scenario 9: Error Handling - No Match in FatSecret

**Objective**: Test handling when food is not found

1. Send: `Съел хренозавр 100г` (nonsense food)

**Expected Flow**:
1. Bot searches FatSecret
2. No results found
3. Bot responds with error or suggestion:
   - "Продукт не найден. Попробуйте переформулировать."
   - OR suggest custom food creation (if implemented)

---

### Scenario 10: Error Handling - API Failures

**Objective**: Test graceful degradation

**Test A: Stop FatSecret MCP Server**
```bash
# In another terminal
docker-compose stop mcp-fatsecret
```

Then send: `Съел яйца`

**Expected**: Error message to user, logged error in agent-api

**Test B: Invalid OpenAI Key**
1. Temporarily set wrong OPENAI_API_KEY in .env
2. Restart services
3. Send: `Съел яйца`

**Expected**: Error message, parsing failure logged

**Recovery**:
```bash
# Fix .env and restart
./scripts/stop.sh
./scripts/startup.sh
```

---

## Performance Benchmarks

### Latency Targets

Test with: `time` in terminal or check logs for processing time

1. **Text Input → Response**
   - Target: < 6 seconds (p95)
   - Measure: Send "Съел 2 яйца 100г" → time until response

2. **Database Query (Reports)**
   - Target: < 2 seconds (p95)
   - Measure: Send `/today` → time until response

3. **FatSecret Search**
   - Target: < 3 seconds
   - Check logs: `docker-compose logs agent-api | grep "fatsecret_search"`

---

## Database Inspection Commands

### Check User Count
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT COUNT(*) FROM user_profile;"
```

### View Recent Food Entries
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT food_name, calories, protein, consumed_at FROM food_log_entry ORDER BY consumed_at DESC LIMIT 10;"
```

### View Daily Totals
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT
     u.telegram_id,
     DATE(f.consumed_at) as date,
     SUM(f.calories) as total_calories,
     SUM(f.protein) as total_protein,
     COUNT(*) as entry_count
   FROM food_log_entry f
   JOIN user_profile u ON f.user_id = u.id
   GROUP BY u.telegram_id, DATE(f.consumed_at)
   ORDER BY date DESC
   LIMIT 7;"
```

### Check Active Conversations
```bash
docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
  "SELECT conversation_id, current_node, is_active, created_at FROM conversation_state WHERE is_active = true;"
```

---

## Common Issues & Solutions

### Issue 1: Bot not responding

**Symptoms**: Send message, no response

**Debug Steps**:
1. Check bot logs:
   ```bash
   docker-compose logs telegram-bot
   ```
2. Look for connection errors
3. Verify TELEGRAM_BOT_TOKEN is correct
4. Check if bot is running:
   ```bash
   docker-compose ps telegram-bot
   ```

**Solution**:
- Verify token with @BotFather
- Restart bot: `docker-compose restart telegram-bot`

---

### Issue 2: "User not found" error

**Symptoms**: `/today` or `/week` returns 404

**Cause**: User not in database

**Solution**:
1. Send `/start` to register
2. Check database:
   ```bash
   docker-compose exec postgres psql -U nutrition_user -d nutrition_bot -c \
     "SELECT * FROM user_profile WHERE telegram_id = YOUR_ID;"
   ```

---

### Issue 3: Food not being saved

**Symptoms**: Get response but database has no entries

**Debug Steps**:
1. Check agent-api logs:
   ```bash
   docker-compose logs agent-api | grep ERROR
   ```
2. Check if LangGraph reached save_entry node:
   ```bash
   docker-compose logs agent-api | grep "save_entry"
   ```

**Common Causes**:
- FatSecret search failed
- Nutrition data missing
- Database connection issue

---

### Issue 4: Migrations failed

**Symptoms**: "relation does not exist" errors

**Solution**:
```bash
# Check migration status
docker-compose exec agent-api alembic current

# Run migrations
docker-compose exec agent-api alembic upgrade head

# If stuck, reset (⚠️ deletes all data)
docker-compose down -v
./scripts/startup.sh
```

---

## Monitoring & Logs

### View All Logs
```bash
docker-compose logs -f
```

### View Specific Service
```bash
docker-compose logs -f agent-api
docker-compose logs -f telegram-bot
docker-compose logs -f postgres
```

### Grep for Errors
```bash
docker-compose logs | grep ERROR
docker-compose logs | grep WARN
```

### Follow Graph Execution
```bash
docker-compose logs -f agent-api | grep "Executing node"
```

---

## Success Criteria

### MVP Acceptance Checklist

- [ ] User can register with `/start`
- [ ] User can log food via text input
- [ ] Bot asks clarifications when needed
- [ ] FatSecret search returns results
- [ ] Inline keyboards work for clarifications
- [ ] Food entries are saved to database
- [ ] `/today` shows accurate totals
- [ ] `/week` shows 7-day breakdown
- [ ] No crashes or unhandled exceptions
- [ ] Response time < 6 seconds for text input

### Quality Checklist

- [ ] All services start successfully
- [ ] Migrations run without errors
- [ ] No memory leaks (check `docker stats`)
- [ ] Logs are readable and informative
- [ ] Error messages are user-friendly
- [ ] No sensitive data in logs (tokens, API keys)

---

## Next Steps After Testing

1. **Fix Bugs**: Address any issues found during testing
2. **Performance Optimization**: If response times are slow
3. **User Experience**: Improve messages and clarification flow
4. **Phase 2**: Add photo label processing
5. **Production Deployment**: Setup proper hosting, monitoring, backups

---

## Test Report Template

Use this template to document test results:

```
## Test Report - [Date]

### Environment
- OS: macOS/Linux/Windows
- Docker Version:
- Services Version: Latest

### Test Results

| Scenario | Status | Notes |
|----------|--------|-------|
| User Registration | ✅/❌ | |
| Simple Text Input | ✅/❌ | |
| Multiple Foods | ✅/❌ | |
| Inline Keyboards | ✅/❌ | |
| Daily Report | ✅/❌ | |
| Weekly Report | ✅/❌ | |

### Issues Found
1. [Issue description]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce:
   - Expected vs Actual:

### Performance Metrics
- Average text response time: X seconds
- Average report generation: X seconds
- Database query time: X ms

### Recommendations
- [Improvement suggestions]
```

---

## Contact & Support

For issues or questions:
- Check logs first
- Review this testing guide
- Examine LangGraph node execution flow
- Verify API credentials are valid
