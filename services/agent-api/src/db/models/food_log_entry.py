"""
Food Log Entry model.
Stores individual food consumption records with complete nutrition data.
"""

from sqlalchemy import Column, BigInteger, String, Numeric, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..base import Base


class MealType(str, enum.Enum):
    """Meal types for categorizing food entries."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class InputType(str, enum.Enum):
    """Input method for food entry."""
    TEXT = "text"
    PHOTO = "photo"
    CUSTOM = "custom"
    MIXED = "mixed"


class FoodLogEntry(Base):
    """Food log entry model."""

    __tablename__ = "food_log_entry"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # User Reference
    user_id = Column(BigInteger, ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False, index=True)

    # Food Identification
    food_id = Column(String(255), nullable=True)  # FatSecret food_id or custom:UUID
    food_name = Column(String(500), nullable=False)
    brand_name = Column(String(255), nullable=True)
    is_custom = Column(Boolean, default=False, nullable=False)

    # Serving Information
    serving_id = Column(String(255), nullable=True)
    serving_description = Column(String(500), nullable=True)
    serving_size = Column(Numeric(10, 2), nullable=True)
    serving_unit = Column(String(50), nullable=True)
    number_of_servings = Column(Numeric(10, 2), default=1.0, nullable=False)

    # Nutrition Data (calculated: per serving * number_of_servings)
    # Macronutrients
    calories = Column(Numeric(10, 2), nullable=False)
    protein = Column(Numeric(10, 2), nullable=True)  # grams
    carbohydrates = Column(Numeric(10, 2), nullable=True)  # grams
    fat = Column(Numeric(10, 2), nullable=True)  # grams

    # Fat breakdown
    saturated_fat = Column(Numeric(10, 2), nullable=True)
    polyunsaturated_fat = Column(Numeric(10, 2), nullable=True)
    monounsaturated_fat = Column(Numeric(10, 2), nullable=True)
    trans_fat = Column(Numeric(10, 2), nullable=True)

    # Micronutrients
    cholesterol = Column(Numeric(10, 2), nullable=True)  # mg
    sodium = Column(Numeric(10, 2), nullable=True)  # mg
    potassium = Column(Numeric(10, 2), nullable=True)  # mg
    fiber = Column(Numeric(10, 2), nullable=True)  # grams
    sugar = Column(Numeric(10, 2), nullable=True)  # grams

    # Vitamins and Minerals
    vitamin_a = Column(Numeric(10, 2), nullable=True)  # % daily value
    vitamin_c = Column(Numeric(10, 2), nullable=True)  # % daily value
    calcium = Column(Numeric(10, 2), nullable=True)  # % daily value
    iron = Column(Numeric(10, 2), nullable=True)  # % daily value

    # Meal Context
    meal_type = Column(SQLEnum(MealType), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Source Tracking
    input_type = Column(SQLEnum(InputType), nullable=False, default=InputType.TEXT)
    original_input = Column(Text, nullable=True)  # Original user input
    label_scan_id = Column(BigInteger, nullable=True)  # Reference to label_scan if from photo

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<FoodLogEntry(id={self.id}, user_id={self.user_id}, "
            f"food_name={self.food_name}, calories={self.calories}, "
            f"consumed_at={self.consumed_at})>"
        )
