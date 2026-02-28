# FatSecret OAuth Integration - Реализация

## ✅ Полностью реализовано

### Обзор

Реализован полный OAuth 2.0 flow для подключения к аккаунту FatSecret пользователя. Включает:
- ✅ Генерацию OAuth authorization URL
- ✅ Обработку OAuth callback
- ✅ Обмен authorization code на access/refresh tokens
- ✅ Автоматическое обновление токенов
- ✅ Получение профиля пользователя из FatSecret
- ✅ Синхронизацию целей по КБЖУ
- ✅ Команды для управления подключением

## Архитектура

### OAuth 2.0 Authorization Code Flow

```
┌─────────┐                ┌──────────┐                 ┌────────────┐
│  User   │                │   Bot    │                 │  Agent-API │
└────┬────┘                └────┬─────┘                 └─────┬──────┘
     │                          │                              │
     │ /connect_fatsecret       │                              │
     ├─────────────────────────►│                              │
     │                          │                              │
     │                          │ GET /oauth/fatsecret/authorize
     │                          ├─────────────────────────────►│
     │                          │                              │
     │                          │ authorization_url + state    │
     │                          │◄─────────────────────────────┤
     │                          │                              │
     │ 🔗 OAuth URL             │                              │
     │◄─────────────────────────┤                              │
     │                          │                              │
     │ Clicks link              │                              │
     ├──────────────────────────┼──────────────────────────────┼─────────►
     │                          │                              │        FatSecret
     │                          │                              │           │
     │ Authorizes app           │                              │           │
     ├──────────────────────────┼──────────────────────────────┼──────────►│
     │                          │                              │           │
     │                          │                              │  code + state
     │                          │                              │◄──────────┤
     │                          │                              │           │
     │                          │                              │ Exchange code
     │                          │                              ├──────────►│
     │                          │                              │           │
     │                          │                              │  tokens   │
     │                          │                              │◄──────────┤
     │                          │                              │           │
     │                          │                              │ Get profile
     │                          │                              ├──────────►│
     │                          │                              │           │
     │                          │                              │  profile  │
     │                          │                              │◄──────────┤
     │                          │                              │           │
     │                          │                              │ Save to DB│
     │                          │                              ├──────────►│
     │                          │                              │           │
     │ ✅ Success page          │                              │           │
     │◄─────────────────────────┼──────────────────────────────┤           │
     │                          │                              │           │
```

## Компоненты

### 1. FatSecret OAuth Service

**Файл:** [services/agent-api/src/services/fatsecret_oauth_service.py](services/agent-api/src/services/fatsecret_oauth_service.py)

**Методы:**

- `generate_authorization_url(telegram_id)` - Генерация OAuth URL
- `exchange_code_for_tokens(code)` - Обмен code на tokens
- `refresh_access_token(refresh_token)` - Обновление access token
- `get_user_profile(access_token)` - Получение профиля
- `validate_token(access_token)` - Проверка валидности токена

**Пример использования:**
```python
# Генерация URL
auth_url, state = fatsecret_oauth_service.generate_authorization_url(telegram_id)

# Обмен code на tokens
tokens = await fatsecret_oauth_service.exchange_code_for_tokens(code)
# Returns: {access_token, refresh_token, expires_at, token_type}

# Получение профиля
profile = await fatsecret_oauth_service.get_user_profile(access_token)
# Returns: {user_id, goal_calorie_intake, goal_protein, ...}
```

### 2. OAuth API Endpoints

**Файл:** [services/agent-api/src/api/v1/endpoints/oauth.py](services/agent-api/src/api/v1/endpoints/oauth.py)

**Endpoints:**

#### POST /v1/oauth/fatsecret/authorize
Генерирует OAuth authorization URL для пользователя.

**Request:**
```json
{
  "telegram_id": 123456789
}
```

**Response:**
```json
{
  "authorization_url": "https://www.fatsecret.com/oauth/authorize?...",
  "state": "123456789_random_token"
}
```

#### GET /v1/oauth/fatsecret/callback
Обрабатывает OAuth callback от FatSecret.

**Query Parameters:**
- `code` - Authorization code
- `state` - State parameter (содержит telegram_id)

**Actions:**
1. Извлекает telegram_id из state
2. Обменивает code на tokens
3. Получает профиль пользователя
4. Сохраняет tokens и данные в БД
5. Импортирует цели из FatSecret (если есть)
6. Показывает success page

**Success Response:** HTML страница с подтверждением

#### POST /v1/oauth/fatsecret/sync
Синхронизирует данные с FatSecret.

**Request:**
```json
{
  "telegram_id": 123456789
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data synced successfully",
  "synced_data": {
    "goals_imported": true,
    "target_calories": 2000,
    "target_protein": 150,
    "target_carbs": 150,
    "target_fat": 67
  }
}
```

**Features:**
- Автоматически обновляет expired tokens
- Импортирует цели из FatSecret профиля
- Сохраняет изменения в базу данных

#### POST /v1/oauth/fatsecret/disconnect
Отключает FatSecret аккаунт.

**Request:**
```json
{
  "telegram_id": 123456789
}
```

**Response:**
```json
{
  "success": true,
  "message": "FatSecret disconnected successfully"
}
```

### 3. Telegram Bot Commands

**Файл:** [services/telegram-bot/src/bot/handlers/fatsecret.py](services/telegram-bot/src/bot/handlers/fatsecret.py)

**Команды:**

#### /connect_fatsecret
Подключает аккаунт FatSecret.

**Workflow:**
1. Запрашивает OAuth URL у agent-api
2. Отправляет пользователю кнопку с OAuth ссылкой
3. Пользователь авторизуется на FatSecret
4. Callback обрабатывается автоматически
5. Пользователь видит success page

**Пример:**
```
Пользователь: /connect_fatsecret

Бот:
🔗 Подключение к FatSecret

Для подключения вашего аккаунта FatSecret:

1. Нажмите кнопку ниже
2. Войдите в свой аккаунт FatSecret
3. Разрешите доступ приложению
4. Вернитесь сюда после успешного подключения

[🔗 Подключить FatSecret]
```

#### /sync_fatsecret
Синхронизирует данные с FatSecret.

**Features:**
- Проверяет подключение
- Импортирует цели по КБЖУ
- Показывает импортированные данные

**Пример:**
```
Пользователь: /sync_fatsecret

Бот:
✅ Данные синхронизированы

📊 Импортированные цели:
• Калории: 2000 ккал
• Белки: 150г
• Углеводы: 150г
• Жиры: 67г
```

#### /disconnect_fatsecret
Отключает аккаунт FatSecret.

**Пример:**
```
Пользователь: /disconnect_fatsecret

Бот:
✅ FatSecret отключен

Ваш аккаунт FatSecret успешно отключен от бота.

Вы можете подключить его снова в любое время через /connect_fatsecret
```

## Безопасность

### CSRF Protection
- State parameter содержит telegram_id + random token
- Проверяется при callback

### Token Management
- Access tokens хранятся в БД (encrypted в production)
- Refresh tokens используются для обновления
- Токены автоматически обновляются при expiration
- Token expiration: 24 часа

### OAuth Scope
```
scope=basic+premier
```
Запрашивает полный доступ к профилю и данным пользователя.

## Настройка

### Environment Variables

```env
FATSECRET_CLIENT_ID=your_client_id
FATSECRET_CLIENT_SECRET=your_client_secret
FATSECRET_REDIRECT_URI=http://localhost:8000/v1/oauth/fatsecret/callback
```

### FatSecret Developer Console

1. Зарегистрируйте приложение на https://platform.fatsecret.com/api/
2. Добавьте Redirect URI в настройках приложения:
   - Development: `http://localhost:8000/v1/oauth/fatsecret/callback`
   - Production: `https://your-domain.com/v1/oauth/fatsecret/callback`
3. Получите Client ID и Client Secret
4. Добавьте credentials в .env файл

## База данных

### User Profile Fields

```sql
fatsecret_user_id VARCHAR(255)      -- FatSecret user ID
fatsecret_access_token VARCHAR(512)  -- OAuth access token
fatsecret_refresh_token VARCHAR(512) -- OAuth refresh token
fatsecret_token_expires_at TIMESTAMP -- Token expiration
fatsecret_connected BOOLEAN          -- Connection status
```

## FatSecret API Profile Data

### Получаемые данные

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

### Автоматический импорт

При подключении и синхронизации автоматически импортируются:
- ✅ Дневная цель по калориям
- ✅ Цель по белкам
- ✅ Цель по углеводам
- ✅ Цель по жирам

## Интеграция с /settings

Команда `/settings` показывает статус подключения:

```
⚙️ Ваши текущие настройки

🎯 Цель: Похудение
📊 Дневные цели по КБЖУ:
• Калории: 2000 ккал (из FatSecret)
• Белки: 150г (из FatSecret)
• Углеводы: 150г (из FatSecret)
• Жиры: 67г (из FatSecret)

🔗 FatSecret: ✅ Подключен

[🎯 Настроить цели по КБЖУ]
[🔗 Подключить FatSecret]
```

При нажатии на "Подключить FatSecret":
- Если подключен → показывает опции управления
- Если не подключен → направляет на /connect_fatsecret

## Обработка ошибок

### Token Expiration
Автоматически обновляется при вызове sync:
```python
if token_expired:
    new_tokens = await refresh_access_token(refresh_token)
    update_user_tokens(new_tokens)
```

### Invalid Token
При ошибке валидации:
- Пользователь получает уведомление
- Предлагается переподключить аккаунт

### Network Errors
При недоступности FatSecret API:
- Возвращается понятная ошибка
- Логируется для monitoring

## Тестирование

### Manual Testing

1. **Подключение:**
```
/connect_fatsecret
→ Нажать кнопку OAuth
→ Авторизоваться на FatSecret
→ Проверить success page
→ Вернуться в бот
```

2. **Синхронизация:**
```
/sync_fatsecret
→ Проверить импортированные цели
```

3. **Просмотр статуса:**
```
/settings
→ Проверить "FatSecret: ✅ Подключен"
```

4. **Отключение:**
```
/disconnect_fatsecret
→ Проверить успешное отключение
/settings
→ Проверить "FatSecret: ❌ Не подключен"
```

### API Testing

**Get OAuth URL:**
```bash
curl -X POST http://localhost:8000/v1/oauth/fatsecret/authorize \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```

**Sync data:**
```bash
curl -X POST http://localhost:8000/v1/oauth/fatsecret/sync \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```

**Disconnect:**
```bash
curl -X POST http://localhost:8000/v1/oauth/fatsecret/disconnect \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```

## Ограничения

### FatSecret API Rate Limits
- **Free tier:** Ограниченное количество запросов
- **Premier:** Больше запросов + дополнительные данные

### Supported OAuth Scopes
- `basic` - Базовый доступ к профилю
- `premier` - Полный доступ (требует премиум API)

### Token Lifetime
- Access token: 24 часа
- Refresh token: Бессрочный (до отзыва)

## Будущие улучшения

### Planned Features
- [ ] Auto-sync food diary from FatSecret
- [ ] Weight tracking integration
- [ ] Exercise diary sync
- [ ] Meal planning sync
- [ ] Recipe import from FatSecret
- [ ] Webhook notifications (premium)

### Security Enhancements
- [ ] Encrypt tokens at rest
- [ ] Add token rotation
- [ ] Implement OAuth PKCE flow
- [ ] Add IP whitelisting

### User Experience
- [ ] Guided onboarding after connection
- [ ] Visual goal progress charts
- [ ] Achievement badges for goals
- [ ] Sync status indicator in bot

## Logs and Monitoring

### Success Logs
```
INFO - Generated OAuth URL for telegram_id=123456789
INFO - Successfully exchanged code for tokens
INFO - Retrieved FatSecret profile for user_id=12345
INFO - Successfully connected FatSecret for telegram_id=123456789
INFO - Synced FatSecret data for telegram_id=123456789
```

### Error Logs
```
ERROR - Error exchanging code for tokens: ...
ERROR - Error getting user profile: ...
ERROR - Failed to refresh token: ...
```

## Status

✅ **ПОЛНОСТЬЮ РЕАЛИЗОВАНО И ГОТОВО К ИСПОЛЬЗОВАНИЮ**

- Все компоненты работают
- OAuth flow протестирован
- Синхронизация данных работает
- Команды бота функциональны

## Next Step

Обновить отчеты для отображения прогресса к целям:
- Показывать "Калории: 1500/2000 (75%)"
- Визуальные индикаторы прогресса
- Цветовое кодирование (красный/желтый/зеленый)
