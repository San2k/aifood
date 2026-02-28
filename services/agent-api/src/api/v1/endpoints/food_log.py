"""
Food log management endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from ....db.session import get_db
from ....db.repositories.user_repository import UserRepository
from ....db.repositories.food_log_repository import FoodLogRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class FoodLogEntryResponse(BaseModel):
    """Response schema for food log entry."""
    id: int
    food_name: str
    brand_name: Optional[str]
    calories: float
    protein: Optional[float]
    carbohydrates: Optional[float]
    fat: Optional[float]
    serving_description: Optional[str]
    number_of_servings: float
    consumed_at: datetime
    meal_type: Optional[str]


@router.get("/users/{telegram_id}/food-log")
async def get_food_log_entries(
    telegram_id: int,
    target_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get food log entries for a user by date.

    Args:
        telegram_id: Telegram user ID
        target_date: Target date (YYYY-MM-DD format), defaults to today
        db: Database session

    Returns:
        List of food log entries
    """
    try:
        user_repo = UserRepository(db)
        food_log_repo = FoodLogRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Parse target date or use today
        if target_date:
            parsed_date = datetime.fromisoformat(target_date).date()
        else:
            parsed_date = date.today()

        entries = await food_log_repo.get_entries_by_date(user.id, parsed_date)

        return {
            "success": True,
            "date": parsed_date.isoformat(),
            "entries": [
                {
                    "id": entry.id,
                    "food_name": entry.food_name,
                    "brand_name": entry.brand_name,
                    "calories": float(entry.calories),
                    "protein": float(entry.protein) if entry.protein else None,
                    "carbohydrates": float(entry.carbohydrates) if entry.carbohydrates else None,
                    "fat": float(entry.fat) if entry.fat else None,
                    "serving_description": entry.serving_description,
                    "number_of_servings": float(entry.number_of_servings),
                    "consumed_at": entry.consumed_at.isoformat(),
                    "meal_type": entry.meal_type.value if entry.meal_type else None
                }
                for entry in entries
            ],
            "count": len(entries)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting food log entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/food-log/{entry_id}")
async def delete_food_log_entry(
    entry_id: int,
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a food log entry (soft delete).

    Args:
        entry_id: Food log entry ID to delete
        telegram_id: Telegram user ID (for authorization)
        db: Database session

    Returns:
        Success response
    """
    try:
        user_repo = UserRepository(db)
        food_log_repo = FoodLogRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Soft delete the entry
        deleted = await food_log_repo.soft_delete_entry(entry_id, user.id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Food entry not found or already deleted")

        await db.commit()

        logger.info(f"Deleted food log entry {entry_id} for telegram_id={telegram_id}")

        return {
            "success": True,
            "message": "Food entry deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting food log entry: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
