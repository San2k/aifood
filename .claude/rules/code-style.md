# Code Style Rules

## Import Ordering

Порядок импортов в каждом Python-файле:

```python
# 1. Standard library
import logging
import enum
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from decimal import Decimal

# 2. Third-party
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

# 3. Local (relative imports)
from ..schemas.ingest import IngestRequest, IngestResponse
from ....db.session import AsyncSessionLocal
from ....db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
```

## Naming Conventions

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Функции/методы | snake_case | `detect_intent()`, `get_by_telegram_id()` |
| Переменные | snake_case | `pending_entries`, `user_id` |
| Классы | PascalCase | `UserRepository`, `NutritionBotState` |
| Константы | UPPERCASE | `DATABASE_URL`, `OPENAI_MODEL_TEXT` |
| Enum members | UPPERCASE | `BREAKFAST = "breakfast"` |

## Type Hints

Обязательны везде. Используй:
- `Optional[T]` для nullable значений
- `List[T]`, `Dict[K, V]` для коллекций
- `TypedDict` для сложных состояний (с `total=False` для partial updates)

```python
async def get_entries_by_date(
    self,
    user_id: int,
    target_date: date
) -> List[FoodLogEntry]:
    ...
```

## Docstrings

Triple-quoted с секциями Args/Returns:

```python
async def ingest_message(request: IngestRequest) -> IngestResponse:
    """
    Process user message through nutrition bot graph.

    Args:
        request: Ingest request with user message

    Returns:
        IngestResponse with results or clarification requests
    """
```

## Error Handling

### В API endpoints
```python
try:
    result = await some_operation()
except HTTPException:
    raise  # Re-raise HTTP exceptions as-is
except Exception as e:
    logger.error(f"Error doing X: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### В repositories
```python
async def soft_delete_entry(self, entry_id: int, user_id: int) -> bool:
    entry = await self.get_entry_by_id(entry_id, user_id)
    if not entry:
        logger.warning(f"Entry {entry_id} not found for user {user_id}")
        return False
    entry.is_deleted = True
    await self.session.flush()
    return True
```

## Enums

Наследуй от `(str, enum.Enum)` для JSON-сериализации:

```python
class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
```

## Decimal для точности

Используй `Decimal` для нутриентов, не `float`:

```python
calories=Decimal(str(calories)),
protein=Decimal(str(protein)) if protein else None,
```

## Logging

Module-level logger, info для операций, error с `exc_info=True`:

```python
logger = logging.getLogger(__name__)

logger.info(f"Found {len(entries)} entries for user {user_id}")
logger.error(f"Error saving entry: {e}", exc_info=True)
```
