# Настройки пользователя - Реализация

## ✅ Реализовано

### 1. Обновление схемы базы данных

**Добавлены поля в таблицу `user_profile`:**
- `fatsecret_user_id` - ID пользователя в FatSecret
- `fatsecret_access_token` - OAuth access token
- `fatsecret_refresh_token` - OAuth refresh token
- `fatsecret_token_expires_at` - Время истечения токена
- `fatsecret_connected` - Статус подключения к FatSecret

**Миграция:** [002_fatsecret_oauth.py](services/agent-api/migrations/versions/20260203_002_add_fatsecret_oauth.py)

### 2. Команда /settings

**Функциональность:**
- Просмотр текущих целей по КБЖУ
- Интерактивная настройка целей:
  1. Выбор цели (похудение, набор массы, поддержание, здоровье)
  2. Ввод дневного лимита калорий
  3. Ввод целей по белкам (г)
  4. Ввод целей по углеводам (г)
  5. Ввод целей по жирам (г)
- Сохранение настроек в базу данных
- Информация о статусе подключения к FatSecret

**Файлы:**
- [services/telegram-bot/src/bot/handlers/settings.py](services/telegram-bot/src/bot/handlers/settings.py) - Handler команды
- [services/telegram-bot/src/bot/keyboards/inline.py](services/telegram-bot/src/bot/keyboards/inline.py) - Inline клавиатуры

**Использование:**
```
Пользователь: /settings

Бот показывает:
⚙️ Ваши текущие настройки

🎯 Цель: Похудение
📊 Дневные цели по КБЖУ:
• Калории: 2000 ккал
• Белки: 150г
• Углеводы: 150г
• Жиры: 67г

🔗 FatSecret: ❌ Не подключен

[🎯 Настроить цели по КБЖУ]
[🔗 Подключить FatSecret]
```

### 3. API Endpoints

**GET /v1/users/{telegram_id}/profile**
- Получение профиля пользователя
- Возвращает все данные включая цели и статус FatSecret

**PUT /v1/users/{telegram_id}/goals**
- Обновление целей пользователя
- Принимает: goal, target_calories, target_protein, target_carbs, target_fat

**Файлы:**
- [services/agent-api/src/api/v1/endpoints/users.py](services/agent-api/src/api/v1/endpoints/users.py)
- [services/telegram-bot/src/services/agent_client.py](services/telegram-bot/src/services/agent_client.py)

## 🔄 В процессе реализации

### FatSecret OAuth Flow
**Задача:** Реализовать OAuth 2.0 авторизацию для подключения к аккаунту FatSecret

**Компоненты:**
1. Authorization endpoint - генерация OAuth URL
2. Callback endpoint - обработка authorization code
3. Token exchange - получение access/refresh tokens
4. Token refresh - автоматическое обновление токенов

**Архитектура:**
```
Пользователь: /connect_fatsecret
    ↓
Бот: Отправляет OAuth URL с authorization_url
    ↓
Пользователь: Переходит по ссылке, авторизуется в FatSecret
    ↓
FatSecret: Редирект на callback URL с authorization_code
    ↓
Agent API: Обменивает code на access_token + refresh_token
    ↓
БД: Сохраняет токены и fatsecret_user_id
    ↓
Бот: Уведомляет пользователя об успешном подключении
```

## 📋 Запланировано

### 1. Команда /connect_fatsecret
- Генерация OAuth authorization URL
- Отправка пользователю ссылки для авторизации
- Обработка callback после авторизации
- Сохранение токенов в базу данных

### 2. Синхронизация данных профиля
- Импорт целей из FatSecret профиля
- Синхронизация данных о весе и росте
- Синхронизация активности (опционально)
- Импорт food diary (опционально)

### 3. Обновление отчетов
- Показывать прогресс к целям:
  ```
  📊 Сегодня:
  Калории: 1500 / 2000 ккал (75%) ✅
  Белки: 120 / 150г (80%) ⚠️
  Углеводы: 180 / 150г (120%) ❌
  Жиры: 55 / 67г (82%) ✅
  ```

### 4. Команды управления
- `/sync_fatsecret` - Синхронизация данных с FatSecret
- `/disconnect_fatsecret` - Отключение аккаунта
- `/import_goals` - Импорт целей из FatSecret

## 🧪 Тестирование

### Проверка /settings команды

1. **Просмотр текущих настроек:**
```
/settings
```

2. **Настройка целей:**
- Нажать "🎯 Настроить цели по КБЖУ"
- Выбрать цель: "🔥 Похудение"
- Ввести калории: `2000`
- Ввести белки: `150`
- Ввести углеводы: `150`
- Ввести жиры: `67`

3. **Проверка сохранения:**
```
/settings (снова)
```
Должны отобразиться введенные значения.

### Проверка API

**Get profile:**
```bash
curl http://localhost:8000/v1/users/123456789/profile
```

**Update goals:**
```bash
curl -X PUT http://localhost:8000/v1/users/123456789/goals \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "weight_loss",
    "target_calories": 2000,
    "target_protein": 150,
    "target_carbs": 150,
    "target_fat": 67
  }'
```

## 🔑 FatSecret OAuth - Technical Details

### OAuth 2.0 Authorization Code Flow

**Шаг 1: Authorization Request**
```
https://www.fatsecret.com/oauth/authorize
  ?response_type=code
  &client_id={CLIENT_ID}
  &redirect_uri={REDIRECT_URI}
  &scope=basic+premier
  &state={STATE}
```

**Шаг 2: User Authorization**
- Пользователь логинится в FatSecret
- Подтверждает доступ для приложения

**Шаг 3: Authorization Code Callback**
```
{REDIRECT_URI}?code={AUTHORIZATION_CODE}&state={STATE}
```

**Шаг 4: Token Exchange**
```
POST https://oauth.fatsecret.com/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code={AUTHORIZATION_CODE}
&redirect_uri={REDIRECT_URI}
&client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
```

**Response:**
```json
{
  "access_token": "xxx",
  "refresh_token": "yyy",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

### FatSecret Profile API

**Get User Profile:**
```
GET https://platform.fatsecret.com/rest/server.api
  ?method=profile.get
  &format=json

Headers:
  Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "profile": {
    "user_id": "12345",
    "goal_weight_kg": 75.0,
    "current_weight_kg": 85.0,
    "height_cm": 180,
    "age": 30,
    "gender": "male",
    "goal_calorie_intake": 2000,
    "goal_protein": 150,
    "goal_carbs": 150,
    "goal_fat": 67
  }
}
```

## 📊 Benefits

### Для пользователя:
- ✅ Простая настройка целей по КБЖУ
- ✅ Визуальный прогресс к целям (после реализации отчетов)
- ✅ Интеграция с FatSecret (после OAuth)
- ✅ Автоматический импорт данных профиля

### Для системы:
- ✅ Персонализированные рекомендации на основе целей
- ✅ Умные уведомления о прогрессе
- ✅ Синхронизация с популярным фитнес-сервисом

## 🚀 Next Steps

1. **Immediate (Today):**
   - [ ] Implement OAuth authorization endpoint
   - [ ] Implement OAuth callback handler
   - [ ] Create /connect_fatsecret command

2. **Short-term (This Week):**
   - [ ] Implement FatSecret profile sync
   - [ ] Update reports with goal progress
   - [ ] Add /sync_fatsecret and /disconnect_fatsecret commands

3. **Future:**
   - [ ] Auto-sync food diary from FatSecret
   - [ ] Weight tracking integration
   - [ ] Exercise diary sync
   - [ ] Weekly/monthly goal analytics

## 📝 Notes

- FatSecret OAuth requires a verified redirect URI in developer console
- Premium FatSecret API features require paid subscription (24 languages support)
- Current implementation uses free tier with Russian→English translation
- Tokens expire after 24 hours and need to be refreshed
- Consider implementing webhook for real-time sync (premium feature)
