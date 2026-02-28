# Testing Rules

## Framework

- **pytest** 7.4.4 — основной фреймворк
- **pytest-asyncio** 0.23.3 — async тесты
- **pytest-cov** 4.1.0 — coverage
- **pytest-mock** 3.12.0 — моки
- **faker** 22.5.1 — генерация тестовых данных

## Структура тестов

```
services/agent-api/tests/
├── conftest.py           # Фикстуры
├── test_api/             # API endpoint тесты
│   ├── test_ingest.py
│   ├── test_users.py
│   └── test_reports.py
├── test_graph/           # LangGraph node тесты
│   ├── test_detect_intent.py
│   ├── test_normalize_input.py
│   └── test_save_entry.py
└── test_services/        # Service unit тесты
    ├── test_llm_service.py
    └── test_mcp_client.py
```

## Запуск тестов

```bash
# Все тесты
docker-compose exec agent-api pytest

# С coverage
docker-compose exec agent-api pytest --cov=src --cov-report=html

# Конкретный файл
docker-compose exec agent-api pytest tests/test_api/test_ingest.py

# С verbose output
docker-compose exec agent-api pytest -v

# Только failed тесты
docker-compose exec agent-api pytest --lf
```

## Async тесты

Используй декоратор `@pytest.mark.asyncio`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ingest_message(async_client: AsyncClient):
    response = await async_client.post(
        "/v1/ingest",
        json={
            "telegram_id": 123456,
            "message": "2 яйца",
            "message_id": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
```

## Фикстуры (conftest.py)

```python
import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()

@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def user_data():
    return {
        "telegram_id": fake.random_int(min=100000, max=999999),
        "username": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name()
    }

@pytest.fixture
async def test_user(db_session: AsyncSession, user_data):
    repo = UserRepository(db_session)
    user, _ = await repo.get_or_create_user(**user_data)
    await db_session.commit()
    return user
```

## Моки

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_detect_intent_with_mock(mocker):
    mock_llm = mocker.patch(
        "src.services.llm_service.llm_service.detect_intent",
        new_callable=AsyncMock
    )
    mock_llm.return_value = {
        "intent": "food_entry",
        "confidence": 0.95
    }

    state = {"raw_input": "2 яйца на завтрак"}
    result = await detect_intent(state)

    assert result["detected_intent"] == "food_entry"
    mock_llm.assert_called_once()
```

## Assertions

```python
# Проверка структуры ответа
assert "parsed_foods" in result
assert isinstance(result["parsed_foods"], list)
assert len(result["parsed_foods"]) > 0

# Проверка нутриентов
assert result["calories"] > 0
assert result["protein"] >= 0

# Проверка ошибок
assert response.status_code == 404
assert "not found" in response.json()["detail"].lower()
```
