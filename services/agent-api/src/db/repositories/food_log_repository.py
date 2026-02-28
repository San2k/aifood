"""
Food Log Repository.
Handles CRUD operations for food log entries.
"""

import logging
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from ..models.food_log_entry import FoodLogEntry, MealType, InputType

logger = logging.getLogger(__name__)


class FoodLogRepository:
    """Repository for food log operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_entry(
        self,
        user_id: int,
        food_name: str,
        calories: float,
        consumed_at: datetime,
        food_id: Optional[str] = None,
        brand_name: Optional[str] = None,
        serving_id: Optional[str] = None,
        serving_description: Optional[str] = None,
        serving_size: Optional[float] = None,
        serving_unit: Optional[str] = None,
        number_of_servings: float = 1.0,
        protein: Optional[float] = None,
        carbohydrates: Optional[float] = None,
        fat: Optional[float] = None,
        fiber: Optional[float] = None,
        sugar: Optional[float] = None,
        sodium: Optional[float] = None,
        meal_type: Optional[str] = None,
        input_type: str = "text",
        original_input: Optional[str] = None,
        is_custom: bool = False,
        **kwargs
    ) -> FoodLogEntry:
        """
        Create a new food log entry.
        
        Args:
            user_id: User ID
            food_name: Name of the food
            calories: Calories
            consumed_at: When the food was consumed
            **kwargs: Additional nutrition data
            
        Returns:
            Created FoodLogEntry
        """
        entry = FoodLogEntry(
            user_id=user_id,
            food_id=food_id,
            food_name=food_name,
            brand_name=brand_name,
            is_custom=is_custom,
            serving_id=serving_id,
            serving_description=serving_description,
            serving_size=Decimal(str(serving_size)) if serving_size else None,
            serving_unit=serving_unit,
            number_of_servings=Decimal(str(number_of_servings)),
            calories=Decimal(str(calories)),
            protein=Decimal(str(protein)) if protein else None,
            carbohydrates=Decimal(str(carbohydrates)) if carbohydrates else None,
            fat=Decimal(str(fat)) if fat else None,
            fiber=Decimal(str(fiber)) if fiber else None,
            sugar=Decimal(str(sugar)) if sugar else None,
            sodium=Decimal(str(sodium)) if sodium else None,
            meal_type=MealType(meal_type) if meal_type else None,
            consumed_at=consumed_at,
            input_type=InputType(input_type),
            original_input=original_input
        )
        
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        
        logger.info(f"Created food log entry: {entry.id} - {food_name}")
        return entry
    
    async def get_entries_by_date(
        self,
        user_id: int,
        target_date: date
    ) -> List[FoodLogEntry]:
        """
        Get all food entries for a specific date.
        
        Args:
            user_id: User ID
            target_date: Target date
            
        Returns:
            List of food log entries
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        stmt = select(FoodLogEntry).where(
            and_(
                FoodLogEntry.user_id == user_id,
                FoodLogEntry.consumed_at >= start_datetime,
                FoodLogEntry.consumed_at <= end_datetime,
                FoodLogEntry.is_deleted == False
            )
        ).order_by(FoodLogEntry.consumed_at)
        
        result = await self.session.execute(stmt)
        entries = result.scalars().all()
        
        logger.info(f"Found {len(entries)} entries for user {user_id} on {target_date}")
        return list(entries)
    
    async def calculate_daily_totals(
        self,
        user_id: int,
        target_date: date
    ) -> dict:
        """
        Calculate nutrition totals for a day.
        
        Args:
            user_id: User ID
            target_date: Target date
            
        Returns:
            Dictionary with nutrition totals
        """
        entries = await self.get_entries_by_date(user_id, target_date)
        
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbohydrates": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sugar": 0.0,
            "sodium": 0.0,
            "entry_count": len(entries)
        }
        
        for entry in entries:
            totals["calories"] += float(entry.calories) if entry.calories else 0
            totals["protein"] += float(entry.protein) if entry.protein else 0
            totals["carbohydrates"] += float(entry.carbohydrates) if entry.carbohydrates else 0
            totals["fat"] += float(entry.fat) if entry.fat else 0
            totals["fiber"] += float(entry.fiber) if entry.fiber else 0
            totals["sugar"] += float(entry.sugar) if entry.sugar else 0
            totals["sodium"] += float(entry.sodium) if entry.sodium else 0
        
        logger.info(f"Calculated daily totals for user {user_id}: {totals['calories']} kcal")
        return totals

    async def get_entry_by_id(
        self,
        entry_id: int,
        user_id: int
    ) -> Optional[FoodLogEntry]:
        """
        Get a specific food log entry by ID.

        Args:
            entry_id: Entry ID
            user_id: User ID (for security check)

        Returns:
            FoodLogEntry or None if not found
        """
        stmt = select(FoodLogEntry).where(
            and_(
                FoodLogEntry.id == entry_id,
                FoodLogEntry.user_id == user_id,
                FoodLogEntry.is_deleted == False
            )
        )

        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        return entry

    async def soft_delete_entry(
        self,
        entry_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete a food log entry.

        Args:
            entry_id: Entry ID to delete
            user_id: User ID (for security check)

        Returns:
            True if deleted, False if not found
        """
        entry = await self.get_entry_by_id(entry_id, user_id)

        if not entry:
            logger.warning(f"Entry {entry_id} not found for user {user_id}")
            return False

        entry.is_deleted = True
        await self.session.flush()

        logger.info(f"Soft deleted food log entry: {entry_id} - {entry.food_name}")
        return True
