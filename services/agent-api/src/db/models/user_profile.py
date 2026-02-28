"""
User Profile model.
Stores user information, goals, and preferences.
"""

from sqlalchemy import Column, BigInteger, String, Integer, Numeric, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional
import enum

from ..base import Base


class UserGoal(str, enum.Enum):
    """User nutrition goals."""
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    HEALTH = "health"


class ActivityLevel(str, enum.Enum):
    """User activity levels."""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class MeasurementSystem(str, enum.Enum):
    """Measurement systems."""
    METRIC = "metric"
    IMPERIAL = "imperial"


class UserProfile(Base):
    """User profile model."""

    __tablename__ = "user_profile"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Telegram Info
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # User Goals
    goal = Column(SQLEnum(UserGoal), nullable=True, default=UserGoal.MAINTENANCE)
    target_calories = Column(Integer, nullable=True)
    target_protein = Column(Integer, nullable=True)  # grams
    target_carbs = Column(Integer, nullable=True)  # grams
    target_fat = Column(Integer, nullable=True)  # grams
    target_fiber = Column(Integer, nullable=True)  # grams

    # User Metrics
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other
    height_cm = Column(Numeric(5, 2), nullable=True)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    activity_level = Column(SQLEnum(ActivityLevel), nullable=True, default=ActivityLevel.MODERATELY_ACTIVE)

    # Preferences
    timezone = Column(String(50), nullable=False, default="UTC")
    language_code = Column(String(10), nullable=False, default="en")
    measurement_system = Column(SQLEnum(MeasurementSystem), nullable=False, default=MeasurementSystem.METRIC)

    # FatSecret Integration
    fatsecret_user_id = Column(String(255), nullable=True, index=True)
    fatsecret_access_token = Column(String(512), nullable=True)
    fatsecret_refresh_token = Column(String(512), nullable=True)
    fatsecret_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    fatsecret_connected = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    weight_history = relationship("WeightHistory", back_populates="user", cascade="all, delete-orphan", order_by="WeightHistory.measured_at.desc()")

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
