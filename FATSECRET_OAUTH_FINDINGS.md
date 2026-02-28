# FatSecret OAuth - Критические находки из документации

## Проблема

Текущая реализация OAuth для подключения пользовательских аккаунтов FatSecret **несовместима** с тем, что предоставляет FatSecret API.

## Что обнаружено в официальной документации

### OAuth 2.0 на FatSecret

**Источник:** https://platform.fatsecret.com/docs/guides/authentication/oauth2

**Поддерживаемые grant types:**
```
✅ client_credentials ТОЛЬКО
❌ authorization_code НЕ поддерживается
❌ implicit НЕ поддерживается
❌ password НЕ поддерживается
```

**Прямая цитата из документации:**
> "We only support 'client_credentials'"

**Что это значит:**
- OAuth 2.0 используется ТОЛЬКО для server-to-server аутентификации
- НЕТ пользовательской авторизации через OAuth 2.0
- НЕТ redirect URIs
- НЕТ authorization codes
- НЕТ user consent screens

### OAuth 1.0 на FatSecret

**Источник:** https://platform.fatsecret.com/docs/guides/authentication/oauth1/three-legged

**Для пользовательской авторизации FatSecret использует:**
- OAuth 1.0a three-legged flow
- HMAC-SHA1 подписи
- Request tokens, Access tokens
- Callback URLs (но это OAuth 1.0, не OAuth 2.0)

**Workflow:**
```
1. POST /oauth/request_token → получить request_token
2. Redirect user to /oauth/authorize?oauth_token=xxx
3. User authorizes
4. Callback to your URL with oauth_verifier
5. POST /oauth/access_token → exchange verifier for access_token
```

## Текущая реализация (что сделано)

### Файлы с несовместимой реализацией

**1. services/agent-api/src/services/fatsecret_oauth_service.py**
```python
# Реализует OAuth 2.0 authorization code flow
def generate_authorization_url()
def exchange_code_for_tokens()  # ← НЕ РАБОТАЕТ с FatSecret
```

**2. services/agent-api/src/api/v1/endpoints/oauth.py**
```python
@router.post("/oauth/fatsecret/authorize")
# Генерирует OAuth 2.0 authorization URL - НЕ поддерживается FatSecret

@router.get("/oauth/fatsecret/callback")
# Ожидает code parameter - НЕ существует в FatSecret OAuth 2.0
```

**3. services/telegram-bot/src/bot/handlers/fatsecret.py**
```python
# /connect_fatsecret - использует несуществующий OAuth 2.0 flow
# /sync_fatsecret - требует user access token (недоступен в OAuth 2.0)
```

## Что РАБОТАЕТ

### Client Credentials Flow (OAuth 2.0)

**Тестирование:**
```bash
curl -X POST https://oauth.fatsecret.com/connect/token \
  -u "f30f6672d0b4472e8442d7831ce185f9:e496b3db72d9413fa63f3d98f0f2b3b4" \
  -d "grant_type=client_credentials&scope=basic"
```

**Результат:**
```json
{
  "access_token": "...",
  "expires_in": 86400,
  "token_type": "Bearer",
  "scope": "basic"
}
```

**Что можно делать с этим токеном:**
- ✅ Поиск продуктов (foods.search)
- ✅ Получение информации о продукте (food.get)
- ✅ Получение порций (food.servings)
- ❌ Доступ к пользовательскому профилю
- ❌ Импорт целей пользователя
- ❌ Синхронизация дневника питания

## Варианты решения

### Вариант A: Реализовать OAuth 1.0 Three-Legged Flow

**Плюсы:**
- Полный доступ к пользовательским данным
- Импорт целей по КБЖУ
- Синхронизация дневника питания

**Минусы:**
- Требует полной переписи OAuth сервиса
- OAuth 1.0a сложнее (HMAC подписи)
- Нужна библиотека для OAuth 1.0 (requests-oauthlib)
- Занимает ~2-3 дня разработки

**Файлы для изменения:**
- `services/agent-api/src/services/fatsecret_oauth_service.py` - полная перепись
- `services/agent-api/src/api/v1/endpoints/oauth.py` - изменение flow
- `services/telegram-bot/src/bot/handlers/fatsecret.py` - без изменений (API остается тем же)

**Пример реализации (OAuth 1.0):**
```python
from requests_oauthlib import OAuth1Session

# Step 1: Get request token
oauth = OAuth1Session(
    client_key=FATSECRET_CLIENT_ID,
    client_secret=FATSECRET_CLIENT_SECRET,
    callback_uri=FATSECRET_REDIRECT_URI
)
request_token_url = "https://www.fatsecret.com/oauth/request_token"
fetch_response = oauth.fetch_request_token(request_token_url)

# Step 2: Redirect user
authorization_url = oauth.authorization_url(
    "https://www.fatsecret.com/oauth/authorize"
)

# Step 3: Handle callback
oauth = OAuth1Session(
    client_key=FATSECRET_CLIENT_ID,
    client_secret=FATSECRET_CLIENT_SECRET,
    resource_owner_key=request_token,
    resource_owner_secret=request_token_secret,
    verifier=oauth_verifier
)
access_token_url = "https://www.fatsecret.com/oauth/access_token"
oauth_tokens = oauth.fetch_access_token(access_token_url)
```

### Вариант B: Отключить OAuth пользователей, использовать только Client Credentials

**Плюсы:**
- Ничего не нужно переписывать
- Основной функционал работает (поиск еды)
- Простое решение

**Минусы:**
- ❌ Нет подключения аккаунта FatSecret
- ❌ Нет импорта целей
- ❌ Нет синхронизации данных

**Что оставить:**
- ✅ Поиск продуктов через FatSecret
- ✅ Получение пищевой ценности
- ✅ Ручная настройка целей через /settings
- ✅ Отслеживание питания в боте

**Что убрать:**
- ❌ /connect_fatsecret
- ❌ /sync_fatsecret
- ❌ /disconnect_fatsecret

**Изменения:**
1. Закомментировать OAuth endpoints в `oauth.py`
2. Удалить OAuth handlers из telegram-bot
3. Обновить документацию
4. Добавить заметку в /settings: "FatSecret используется только для поиска продуктов"

### Вариант C: Связаться с FatSecret Support

**Вопрос для поддержки:**
> "Does FatSecret Platform API support OAuth 2.0 authorization code flow for user authentication?
> Our application needs to access user profile data and goals, but we only see client_credentials
> grant type documented. Can we use authorization_code grant type with redirect URIs?"

**Контакты:**
- Email: api@fatsecret.com
- Form: https://www.fatsecret.com/contact/

**Вероятный ответ:**
> "No, OAuth 2.0 is only for server-to-server. Use OAuth 1.0 three-legged flow for user authentication."

## Рекомендация

### Короткосрочное решение (сейчас): Вариант B

**Обоснование:**
1. Client credentials уже работают ✅
2. Основной функционал (поиск еды, логирование) работает ✅
3. Цели можно настроить вручную через /settings ✅
4. Не блокирует дальнейшую разработку
5. Можно вернуться к OAuth 1.0 позже

**Действия:**
1. Обновить `.env` - убрать FATSECRET_REDIRECT_URI (не нужен)
2. Отключить OAuth endpoints (закомментировать routes)
3. Удалить /connect_fatsecret, /sync_fatsecret из бота
4. Обновить /settings - убрать упоминания FatSecret подключения
5. Добавить в README информацию об ограничениях

### Среднесрочное решение (если нужен импорт целей): Вариант A

**Когда реализовать:**
- Если пользователи активно просят импорт целей
- После завершения основного функционала бота
- Когда будет время на тестирование OAuth 1.0

**Оценка времени:** 2-3 дня разработки + 1 день тестирования

## Текущий статус

### Что работает прямо сейчас
```bash
# 1. Client Credentials работают
curl -X POST https://oauth.fatsecret.com/connect/token \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=basic"
# → Returns access_token ✅

# 2. Поиск продуктов работает
# MCP tool search_food() использует client credentials ✅

# 3. Получение данных о продукте работает
# MCP tool get_food() работает ✅
```

### Что НЕ работает
```bash
# 1. OAuth authorization URL
POST /v1/oauth/fatsecret/authorize
# → Генерирует URL для несуществующего OAuth 2.0 flow ❌

# 2. OAuth callback
GET /v1/oauth/fatsecret/callback?code=xxx
# → FatSecret никогда не отправит code (не поддерживается) ❌

# 3. Команды бота
/connect_fatsecret  # → Использует несуществующий flow ❌
/sync_fatsecret     # → Требует user access token (недоступен) ❌
```

## Почему вы не нашли "Redirect URIs" в консоли

**Ответ:** Потому что их там нет для OAuth 2.0 приложений.

FatSecret OAuth 2.0 использует ТОЛЬКО client credentials (server-to-server), где:
- Нет пользовательской авторизации
- Нет redirect URIs
- Нет callback URLs
- Нет user consent screens

Redirect URIs существуют только для OAuth 1.0 three-legged flow, который настраивается по-другому.

## Следующие шаги

### Рекомендуемый путь

**Шаг 1: Принять решение о реализации**
- Вариант B (отключить OAuth) - быстро, работает сейчас
- Вариант A (OAuth 1.0) - полный функционал, но требует времени

**Шаг 2 (если выбран Вариант B):**
1. Удалить OAuth endpoints из agent-api
2. Удалить OAuth команды из telegram-bot
3. Обновить документацию
4. Продолжить разработку основного функционала

**Шаг 3 (если выбран Вариант A):**
1. Изучить OAuth 1.0 документацию FatSecret
2. Установить requests-oauthlib
3. Переписать fatsecret_oauth_service.py
4. Тестировать three-legged flow
5. Обновить endpoints

## Тестовые команды

### Проверка client credentials (работает)
```bash
curl -X POST https://oauth.fatsecret.com/connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "f30f6672d0b4472e8442d7831ce185f9:e496b3db72d9413fa63f3d98f0f2b3b4" \
  -d "grant_type=client_credentials&scope=basic"
```

### Проверка поиска продуктов (работает через MCP)
```bash
# В agent-api через MCP FatSecret
# Использует client credentials автоматически
```

## Вывод

**FatSecret API:**
- ✅ Client Credentials (OAuth 2.0) - работает для поиска продуктов
- ❌ Authorization Code (OAuth 2.0) - НЕ поддерживается
- ⏳ Three-Legged Flow (OAuth 1.0) - поддерживается, но не реализовано

**Текущая реализация:**
- ✅ Поиск продуктов - работает
- ✅ Получение пищевой ценности - работает
- ❌ Подключение пользовательского аккаунта - не работает (несовместимый flow)
- ❌ Импорт целей - не работает (требует user access token)

**Рекомендация:** Использовать Вариант B (отключить OAuth пользователей) для MVP, реализовать OAuth 1.0 позже если потребуется импорт целей.
