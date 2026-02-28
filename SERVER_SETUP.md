# Server Setup Guide

Инструкция по настройке VPS для автодеплоя AiFood.

## 1. Требования

- Ubuntu 22.04+ или Debian 12+
- Docker & Docker Compose
- Git
- 2GB+ RAM, 20GB+ disk

## 2. Начальная настройка сервера

```bash
# Создаём директорию проекта
sudo mkdir -p /opt/aifood
sudo chown $USER:$USER /opt/aifood

# Клонируем репозиторий
cd /opt
git clone https://github.com/San2k/aifood.git aifood
cd aifood

# Создаём production .env
cp .env.example .env.prod
nano .env.prod  # Заполнить реальными значениями
```

## 3. Настройка .env.prod

```bash
# Database (уникальные пароли!)
POSTGRES_USER=nutrition_user
POSTGRES_PASSWORD=СГЕНЕРИРОВАТЬ_СИЛЬНЫЙ_ПАРОЛЬ
POSTGRES_DB=nutrition_bot

# Telegram
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_TEXT=gpt-4-turbo-preview
OPENAI_MODEL_VISION=gpt-4o

# FatSecret
FATSECRET_CLIENT_ID=ваш_client_id
FATSECRET_CLIENT_SECRET=ваш_client_secret

# Other
LLM_PROVIDER=openai
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## 4. Первый запуск

```bash
cd /opt/aifood

# Запуск
docker-compose -f docker-compose.prod.yml up -d

# Подождать запуска
sleep 15

# Миграции БД
docker-compose -f docker-compose.prod.yml exec agent-api alembic upgrade head

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

## 5. Настройка GitHub Actions (автодеплой)

В репозитории GitHub → Settings → Secrets and variables → Actions:

| Secret | Описание |
|--------|----------|
| `VPS_HOST` | IP адрес сервера |
| `VPS_USER` | SSH пользователь (не root!) |
| `VPS_SSH_KEY` | Приватный SSH ключ |
| `VPS_PORT` | SSH порт (по умолчанию 22) |

### Создание SSH ключа для деплоя

```bash
# На локальной машине
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/aifood_deploy

# Скопировать публичный ключ на сервер
ssh-copy-id -i ~/.ssh/aifood_deploy.pub user@your-server

# Приватный ключ добавить в GitHub Secrets как VPS_SSH_KEY
cat ~/.ssh/aifood_deploy
```

## 6. Полезные команды на сервере

```bash
cd /opt/aifood

# Логи
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Обновление вручную
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec agent-api alembic upgrade head

# Статус
docker-compose -f docker-compose.prod.yml ps
```

## 7. Изоляция от других проектов

Проект использует:
- Изолированную Docker network: `aifood_network`
- Именованные volumes: `aifood_postgres_data`, `aifood_redis_data`
- Уникальные имена контейнеров: `aifood_*`

Это гарантирует отсутствие конфликтов с другими Docker проектами на сервере.

## 8. Бэкапы базы данных

```bash
# Создать бэкап
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U nutrition_user nutrition_bot > backup_$(date +%Y%m%d).sql

# Восстановить
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U nutrition_user nutrition_bot < backup_20240101.sql
```

## 9. Мониторинг

```bash
# Проверка health
curl http://localhost:8000/health

# Использование ресурсов
docker stats aifood_agent_api aifood_telegram_bot aifood_postgres aifood_redis
```
