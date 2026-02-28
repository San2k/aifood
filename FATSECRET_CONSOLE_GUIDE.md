# FatSecret Developer Console - Подробная инструкция

## Где находится настройка Redirect URI

### Вариант 1: Platform.fatsecret.com (Основной интерфейс)

1. **Зайдите на https://platform.fatsecret.com/api/**
2. **Войдите в аккаунт** (если не вошли)
3. Вы должны увидеть главную страницу с разделами:
   - **API Keys** (или "My API Keys")
   - **Applications**
   - **Documentation**

#### Если видите раздел "API Keys":

1. Нажмите **"API Keys"** в левом меню или на главной странице
2. Вы увидите список ваших API ключей
3. Найдите ваше приложение (по Client ID: `f30f6672d0b4472e8442d7831ce185f9`)
4. Нажмите на название приложения или **"Manage"** / **"Edit"**
5. В открывшейся странице найдите раздел **"OAuth Redirect URIs"** или **"Redirect URIs"**
6. Нажмите **"Add Redirect URI"** или **"Add"**
7. Введите ваш ngrok URL

#### Если видите раздел "My Applications":

1. Нажмите **"My Applications"**
2. Выберите ваше приложение
3. Перейдите на вкладку **"OAuth"** или **"Settings"**
4. Найдите **"Redirect URIs"**
5. Добавьте URL

### Вариант 2: Старый интерфейс (fatsecret.com/oauth)

Если вы на старой версии консоли:

1. Зайдите на https://www.fatsecret.com/oauth/
2. Войдите в аккаунт
3. Нажмите **"Register Application"** (если приложение не создано)
4. Или найдите ваше существующее приложение в списке
5. Нажмите **"Edit"** рядом с приложением
6. Найдите поле **"Callback URL"** или **"Redirect URI"**
7. Добавьте URL

### Вариант 3: Через API Management Console

1. https://platform.fatsecret.com/api/Default.aspx
2. В меню слева: **"My Keys"** или **"API Keys"**
3. Найдите ваше приложение
4. Нажмите **"Edit Application"**
5. Добавьте Redirect URI

## Что делать, если НЕ ВИДИТЕ где добавить Redirect URI

### Возможная причина 1: OAuth не включен для приложения

FatSecret может требовать явного включения OAuth:

1. В настройках приложения найдите **"OAuth Settings"**
2. Включите **"Enable OAuth"** или **"OAuth 2.0"**
3. После этого появится поле для Redirect URI

### Возможная причина 2: Тип приложения

Некоторые типы приложений не поддерживают OAuth redirect:

1. При создании приложения выберите тип: **"Web Application"** (не "Desktop" или "Mobile")
2. Только Web Applications поддерживают OAuth redirect flow

### Возможная причина 3: Нужен премиум аккаунт

Если OAuth с redirect URI требует Premier API:

**ВРЕМЕННОЕ РЕШЕНИЕ:** Используйте Client Credentials flow (без redirect)

## Альтернативное решение БЕЗ OAuth redirect

Если FatSecret не позволяет добавить Redirect URI, можно использовать упрощенный метод:

### Client Credentials Flow (без пользовательской авторизации)

Это уже работает в вашем боте! API ключи используются для:
- Поиск продуктов
- Получение информации о питании

**НО:** Без OAuth redirect НЕ будет работать:
- ❌ Подключение аккаунта пользователя
- ❌ Импорт целей из FatSecret
- ❌ Синхронизация данных

**Будет работать:**
- ✅ Поиск еды
- ✅ Получение пищевой ценности
- ✅ Ручная настройка целей через /settings
- ✅ Отслеживание питания

## Скриншоты для поиска

Ищите на странице:
- "Redirect URI"
- "Callback URL"
- "OAuth Redirect"
- "Authorized Redirect URIs"
- "OAuth Settings"
- "OAuth 2.0 Configuration"

## Быстрая проверка типа приложения

Выполните в терминале:
```bash
curl -X POST https://oauth.fatsecret.com/connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=basic" \
  -u "f30f6672d0b4472e8442d7831ce185f9:e496b3db72d9413fa63f3d98f0f2b3b4"
```

Если вернет access_token - приложение настроено корректно.

## Что делать дальше?

### Сценарий A: OAuth redirect НЕ доступен

**Решение:** Отключить функции, требующие OAuth

1. Отключить команды:
   - `/connect_fatsecret` (не будет работать)
   - `/sync_fatsecret` (не будет работать)
   - `/disconnect_fatsecret` (не будет работать)

2. Использовать только:
   - `/settings` - ручная настройка целей
   - Поиск еды через FatSecret API
   - Отслеживание питания

### Сценарий B: OAuth redirect доступен

После добавления Redirect URI в консоли:

1. Обновите .env с ngrok URL
2. Перезапустите agent-api
3. Протестируйте `/connect_fatsecret`

## Контакты поддержки FatSecret

Если не можете найти настройки:
- Email: api@fatsecret.com
- Форма: https://www.fatsecret.com/contact/

Спросите: "How do I add OAuth Redirect URI for my application?"

## Текущий статус вашего приложения

Client ID: `f30f6672d0b4472e8442d7831ce185f9`

Проверим, что уже работает:
```bash
# Test 1: Client Credentials
curl -X POST https://oauth.fatsecret.com/connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "f30f6672d0b4472e8442d7831ce185f9:e496b3db72d9413fa63f3d98f0f2b3b4" \
  -d "grant_type=client_credentials&scope=basic"

# Test 2: Food Search (should work)
curl http://localhost:8000/v1/oauth/fatsecret/authorize \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```
