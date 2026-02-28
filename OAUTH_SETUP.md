# FatSecret OAuth Setup - Инструкция по настройке

## Проблема
`localhost:8000` недоступен для FatSecret сервера. OAuth callback требует публичный URL.

## Решение: ngrok туннель

### Шаг 1: Запустите ngrok

Откройте **новый терминал** и выполните:

```bash
cd /Users/sandro/Documents/Other/AiFood
./start_ngrok.sh
```

Или напрямую:
```bash
ngrok http 8000
```

Вы увидите что-то вроде:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

**ВАЖНО:** Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)

### Шаг 2: Обновите .env файл

Откройте `.env` файл и замените:
```env
FATSECRET_REDIRECT_URI=http://localhost:8000/v1/oauth/fatsecret/callback
```

На:
```env
FATSECRET_REDIRECT_URI=https://YOUR_NGROK_URL.ngrok.io/v1/oauth/fatsecret/callback
```

Например:
```env
FATSECRET_REDIRECT_URI=https://abc123.ngrok.io/v1/oauth/fatsecret/callback
```

### Шаг 3: Перезапустите agent-api

```bash
docker-compose restart agent-api
```

### Шаг 4: Добавьте Redirect URI в FatSecret Developer Console

1. Зайдите на https://platform.fatsecret.com/api/
2. Войдите в аккаунт
3. Перейдите в **Your Applications**
4. Выберите ваше приложение
5. Найдите секцию **Redirect URIs**
6. Нажмите **Add Redirect URI**
7. Введите: `https://YOUR_NGROK_URL.ngrok.io/v1/oauth/fatsecret/callback`
8. Нажмите **Save**

### Шаг 5: Протестируйте OAuth

В Telegram боте:
```
/connect_fatsecret
```

Нажмите кнопку "Подключить FatSecret" → авторизуйтесь → вы должны увидеть success страницу ✅

## Важные заметки

### ngrok должен быть запущен
- ngrok создает временный URL
- Если закрыть ngrok, URL перестанет работать
- При перезапуске ngrok URL изменится
- Нужно будет обновить `.env` и FatSecret Developer Console

### Для production
Используйте постоянный домен:
```env
FATSECRET_REDIRECT_URI=https://your-domain.com/v1/oauth/fatsecret/callback
```

## Альтернативы ngrok

### 1. Cloudflare Tunnel (бесплатно, постоянный URL)
```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8000
```

### 2. localtunnel (бесплатно)
```bash
npm install -g localtunnel
lt --port 8000
```

### 3. Реальный deploy (Production)
- Railway.app
- Render.com
- DigitalOcean
- AWS/GCP

## Troubleshooting

### ngrok не запускается
```bash
# Проверьте, не занят ли порт 4040
lsof -ti:4040 | xargs kill -9

# Запустите снова
ngrok http 8000
```

### OAuth callback возвращает 404
- Убедитесь, что agent-api запущен
- Проверьте, что URL в .env совпадает с ngrok URL
- Проверьте, что URL добавлен в FatSecret Developer Console

### "Invalid redirect URI"
- URL в FatSecret Console должен точно совпадать с FATSECRET_REDIRECT_URI
- Включая https:// и /v1/oauth/fatsecret/callback

### Токены не сохраняются
- Проверьте логи: `docker-compose logs agent-api | grep oauth`
- Проверьте, что пользователь существует в базе данных
- Попробуйте `/start` в боте для регистрации

## Быстрая проверка

### Тест 1: ngrok работает
```bash
curl https://YOUR_NGROK_URL.ngrok.io/health
```
Должен вернуть: `{"status":"healthy","service":"agent-api"}`

### Тест 2: OAuth endpoint доступен
```bash
curl https://YOUR_NGROK_URL.ngrok.io/v1/oauth/fatsecret/callback?code=test&state=123_test
```
Должен вернуть HTML страницу (даже с ошибкой - это нормально для теста)

### Тест 3: Authorization URL генерируется
```bash
curl -X POST https://YOUR_NGROK_URL.ngrok.io/v1/oauth/fatsecret/authorize \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 123456789}'
```
Должен вернуть `authorization_url` с ngrok URL в redirect_uri

## Статус

- ✅ OAuth endpoints реализованы
- ✅ HTMLResponse для callback
- ✅ ngrok установлен
- ⏳ Нужно запустить ngrok
- ⏳ Обновить .env
- ⏳ Добавить URL в FatSecret Console

## Следующие шаги

После успешной настройки OAuth:
1. Протестировать полный flow подключения
2. Протестировать синхронизацию данных
3. Обновить отчеты для отображения прогресса к целям
