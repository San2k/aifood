# Architecture Rules

## Микросервисы

```
┌─────────────────┐     HTTP      ┌─────────────────┐
│  telegram-bot   │ ────────────► │    agent-api    │
│   (aiogram 3)   │               │ (FastAPI+Graph) │
└─────────────────┘               └────────┬────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
             ┌───────────┐          ┌───────────┐          ┌─────────────┐
             │ PostgreSQL│          │   Redis   │          │ mcp-fatsecret│
             └───────────┘          └───────────┘          └─────────────┘
```

| Сервис | Путь | Назначение |
|--------|------|------------|
| agent-api | `services/agent-api/` | FastAPI + LangGraph backend |
| telegram-bot | `services/telegram-bot/` | aiogram 3 Telegram bot |
| mcp-fatsecret | `services/mcp-fatsecret/` | MCP сервер для FatSecret API |

## LangGraph Nodes

Каждая нода — async функция:

```python
async def node_name(state: NutritionBotState) -> Dict[str, Any]:
    """
    Node description.

    Args:
        state: Current graph state

    Returns:
        State updates (partial dict)
    """
    # Получение данных из state с defaults
    raw_input = state.get("raw_input", "")
    errors = state.get("errors", [])

    try:
        # Логика ноды
        result = await process_something(raw_input)

        return {
            "processed_data": result,
            "next_node": "next_step",
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error in node: {e}", exc_info=True)
        return {
            "errors": errors + [str(e)],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
```

### Ключевые ноды

| Нода | Файл | Назначение |
|------|------|------------|
| detect_input_type | `graph/nodes/detect_input_type.py` | Определение типа входа |
| detect_intent | `graph/nodes/detect_intent.py` | Определение намерения |
| normalize_input | `graph/nodes/normalize_input.py` | Парсинг текста через LLM |
| fatsecret_search | `graph/nodes/fatsecret_search.py` | Поиск в FatSecret |
| save_entry | `graph/nodes/save_entry.py` | Сохранение в БД |
| calculate_totals | `graph/nodes/calculate_totals.py` | Подсчёт дневных итогов |

## Repository Pattern

```python
class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Naming: get_*, get_*_by_*, create_*, update_*, *_delete_*

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[UserProfile]:
        stmt = select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, **kwargs) -> UserProfile:
        user = UserProfile(telegram_id=telegram_id, **kwargs)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
```

## API Endpoints

FastAPI с dependency injection:

```python
@router.post("/ingest")
async def ingest_message(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db)
) -> IngestResponse:
    """Process user message."""
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_telegram_id(request.telegram_id)
        # ... logic
        await db.commit()
        return IngestResponse(...)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Telegram Handlers

aiogram Router с фильтрами:

```python
router = Router()

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message, state: FSMContext):
    """Handle text messages."""
    user = message.from_user
    text = message.text

    # Получение состояния
    data = await state.get_data()
    conversation_id = data.get("conversation_id")

    # Вызов Agent API
    response = await agent_client.ingest_message(
        telegram_id=user.id,
        message=text,
        ...
    )

    # Сохранение состояния
    await state.update_data(conversation_id=response["conversation_id"])

    # Отправка ответа
    await message.answer(response["reply_text"])
```

### Callback Data Format

Формат: `action:param1:param2`

```python
# Создание
callback_data = f"clarif:{conversation_id}:{option_index}"

# Парсинг
@router.callback_query(F.data.startswith("clarif:"))
async def handle_clarification(callback: CallbackQuery):
    parts = callback.data.split(":")
    conversation_id = parts[1]
    option_index = parts[2]
```

## SQLAlchemy Models

```python
class FoodLogEntry(Base):
    __tablename__ = "food_log_entry"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_profile.id"), nullable=False, index=True)

    # Nutrition data — use Numeric for precision
    calories = Column(Numeric(10, 2), nullable=False)
    protein = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    consumed_at = Column(DateTime(timezone=True), nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
```
