"""
Food log entry repository.
"""
import logging
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.food_log_entry import FoodLogEntry

logger = logging.getLogger(__name__)


class FoodLogRepository:
    """Repository for food log entries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entry(
        self,
        odentity: str,
        food_name: str,
        calories: Decimal,
        protein: Optional[Decimal] = None,
        carbohydrates: Optional[Decimal] = None,
        fat: Optional[Decimal] = None,
        meal_type: Optional[str] = None,
        consumed_at: Optional[datetime] = None,
        food_id: Optional[str] = None,
        custom_product_id: Optional[int] = None,
    ) -> FoodLogEntry:
        """
        Create a new food log entry.

        Args:
            odentity: User identifier
            food_name: Name of food
            calories: Calories consumed
            protein: Protein in grams
            carbohydrates: Carbs in grams
            fat: Fat in grams
            meal_type: breakfast, lunch, dinner, snack
            consumed_at: When food was consumed
            food_id: FatSecret food ID (optional)
            custom_product_id: Custom product ID (optional)

        Returns:
            Created FoodLogEntry
        """
        entry = FoodLogEntry(
            odentity=odentity,
            food_name=food_name,
            calories=calories,
            protein=protein,
            carbohydrates=carbohydrates,
            fat=fat,
            meal_type=meal_type,
            consumed_at=consumed_at or datetime.utcnow(),
            food_id=food_id,
            custom_product_id=custom_product_id,
            is_deleted=False,
        )

        self.session.add(entry)
        await self.session.flush()

        logger.info(f"Created food log entry {entry.id} for {odentity}: {food_name}")

        return entry

    async def get_entry_by_id(self, entry_id: int, odentity: str) -> Optional[FoodLogEntry]:
        """
        Get entry by ID.

        Args:
            entry_id: Entry ID
            odentity: User identifier (for security)

        Returns:
            FoodLogEntry or None
        """
        stmt = select(FoodLogEntry).where(
            and_(
                FoodLogEntry.id == entry_id,
                FoodLogEntry.odentity == odentity,
                FoodLogEntry.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete_entry(self, entry_id: int, odentity: str) -> bool:
        """
        Soft delete an entry.

        Args:
            entry_id: Entry ID
            odentity: User identifier (for security)

        Returns:
            True if deleted, False if not found
        """
        entry = await self.get_entry_by_id(entry_id, odentity)
        if not entry:
            logger.warning(f"Entry {entry_id} not found for user {odentity}")
            return False

        entry.is_deleted = True
        await self.session.flush()

        logger.info(f"Soft deleted entry {entry_id}")
        return True
