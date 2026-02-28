"""
User profile and settings endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from ....db.session import get_db
from ....db.repositories.user_repository import UserRepository
from ....db.repositories.weight_history_repository import WeightHistoryRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateGoalsRequest(BaseModel):
    """Request schema for updating user goals."""
    goal: Optional[str] = Field(None, description="User goal")
    target_calories: Optional[int] = Field(None, description="Target daily calories")
    target_protein: Optional[int] = Field(None, description="Target daily protein (g)")
    target_carbs: Optional[int] = Field(None, description="Target daily carbs (g)")
    target_fat: Optional[int] = Field(None, description="Target daily fat (g)")


class UpdatePhysicalDataRequest(BaseModel):
    """Request schema for updating physical parameters."""
    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[str] = Field(None, description="Gender (male/female/other)")
    height_cm: Optional[float] = Field(None, description="Height in cm")
    weight_kg: Optional[float] = Field(None, description="Weight in kg")
    activity_level: Optional[str] = Field(None, description="Activity level")


class AddWeightRequest(BaseModel):
    """Request schema for adding weight entry."""
    weight_kg: float = Field(..., description="Weight in kg")
    measured_at: Optional[datetime] = Field(None, description="Measurement datetime")
    notes: Optional[str] = Field(None, description="Optional notes")


class WeightHistoryResponse(BaseModel):
    """Response schema for weight history entry."""
    id: int
    weight_kg: float
    measured_at: datetime
    notes: Optional[str]
    created_at: datetime


@router.get("/users/{telegram_id}/profile")
async def get_user_profile(
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile.

    Args:
        telegram_id: Telegram user ID
        db: Database session

    Returns:
        User profile data
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "goal": user.goal.value if user.goal else None,
            "target_calories": user.target_calories,
            "target_protein": user.target_protein,
            "target_carbs": user.target_carbs,
            "target_fat": user.target_fat,
            "target_fiber": user.target_fiber,
            "fatsecret_connected": user.fatsecret_connected,
            "age": user.age,
            "gender": user.gender,
            "height_cm": float(user.height_cm) if user.height_cm else None,
            "weight_kg": float(user.weight_kg) if user.weight_kg else None,
            "activity_level": user.activity_level.value if user.activity_level else None,
            "language_code": user.language_code,
            "timezone": user.timezone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_active_at": user.last_active_at.isoformat() if user.last_active_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{telegram_id}/goals")
async def update_user_goals(
    telegram_id: int,
    request: UpdateGoalsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user goals.

    Args:
        telegram_id: Telegram user ID
        request: Goals update request
        db: Database session

    Returns:
        Success response
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if request.goal is not None:
            user.goal = request.goal

        if request.target_calories is not None:
            user.target_calories = request.target_calories

        if request.target_protein is not None:
            user.target_protein = request.target_protein

        if request.target_carbs is not None:
            user.target_carbs = request.target_carbs

        if request.target_fat is not None:
            user.target_fat = request.target_fat

        # Save changes (SQLAlchemy tracks changes automatically)
        await db.commit()

        logger.info(f"Updated goals for telegram_id={telegram_id}")

        return {
            "success": True,
            "message": "Goals updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user goals: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{telegram_id}/physical")
async def update_physical_data(
    telegram_id: int,
    request: UpdatePhysicalDataRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user physical parameters (age, gender, height, weight, activity level).

    Args:
        telegram_id: Telegram user ID
        request: Physical data update request
        db: Database session

    Returns:
        Success response
    """
    try:
        user_repo = UserRepository(db)
        weight_repo = WeightHistoryRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Track if weight changed to add to history
        old_weight = float(user.weight_kg) if user.weight_kg else None
        new_weight = request.weight_kg

        # Update fields if provided
        if request.age is not None:
            user.age = request.age

        if request.gender is not None:
            user.gender = request.gender

        if request.height_cm is not None:
            user.height_cm = request.height_cm

        if request.weight_kg is not None:
            user.weight_kg = request.weight_kg
            # Add to weight history if weight changed
            if old_weight != new_weight:
                await weight_repo.create_entry(
                    user_id=user.id,
                    weight_kg=new_weight,
                    notes="Обновлено через настройки"
                )

        if request.activity_level is not None:
            user.activity_level = request.activity_level

        await db.commit()

        logger.info(f"Updated physical data for telegram_id={telegram_id}")

        return {
            "success": True,
            "message": "Physical data updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating physical data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/{telegram_id}/weight")
async def add_weight_entry(
    telegram_id: int,
    request: AddWeightRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Add new weight entry.

    Args:
        telegram_id: Telegram user ID
        request: Weight entry request
        db: Database session

    Returns:
        Created weight entry
    """
    try:
        user_repo = UserRepository(db)
        weight_repo = WeightHistoryRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create weight history entry
        entry = await weight_repo.create_entry(
            user_id=user.id,
            weight_kg=request.weight_kg,
            measured_at=request.measured_at,
            notes=request.notes
        )

        # Update user's current weight
        user.weight_kg = request.weight_kg

        await db.commit()

        logger.info(f"Added weight entry for telegram_id={telegram_id}: {request.weight_kg}kg")

        return {
            "success": True,
            "entry": {
                "id": entry.id,
                "weight_kg": float(entry.weight_kg),
                "measured_at": entry.measured_at.isoformat(),
                "notes": entry.notes
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding weight entry: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{telegram_id}/weight/history")
async def get_weight_history(
    telegram_id: int,
    limit: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Get weight history for user.

    Args:
        telegram_id: Telegram user ID
        limit: Maximum number of entries to return
        db: Database session

    Returns:
        List of weight history entries
    """
    try:
        user_repo = UserRepository(db)
        weight_repo = WeightHistoryRepository(db)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        entries = await weight_repo.get_weight_history(user.id, limit=limit)

        # Calculate weight change if we have entries
        weight_change = None
        if len(entries) >= 2:
            latest = float(entries[0].weight_kg)
            oldest = float(entries[-1].weight_kg)
            weight_change = latest - oldest

        return {
            "success": True,
            "entries": [
                {
                    "id": entry.id,
                    "weight_kg": float(entry.weight_kg),
                    "measured_at": entry.measured_at.isoformat(),
                    "notes": entry.notes,
                    "created_at": entry.created_at.isoformat()
                }
                for entry in entries
            ],
            "weight_change": weight_change,
            "count": len(entries)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weight history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
