"""
Food log entry model.
"""
from sqlalchemy import Column, BigInteger, String, Numeric, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func
from ..session import Base


class FoodLogEntry(Base):
    """
    Food log entry - user's food consumption records.
    """
    __tablename__ = 'food_log_entry'

    id = Column(BigInteger, primary_key=True)
    odentity = Column(String(255), nullable=False, index=True)

    # FatSecret or custom product reference
    food_id = Column(String(255), nullable=True)
    custom_product_id = Column(BigInteger, ForeignKey('custom_products.id'), nullable=True, index=True)

    # Food details
    food_name = Column(String(500), nullable=False)

    # Nutrition (as consumed)
    calories = Column(Numeric(10, 2), nullable=False)
    protein = Column(Numeric(10, 2))
    carbohydrates = Column(Numeric(10, 2))
    fat = Column(Numeric(10, 2))

    # Meal context
    meal_type = Column(String(20))  # breakfast, lunch, dinner, snack

    # Timestamps
    consumed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False, server_default='false')

    def __repr__(self):
        return f"<FoodLogEntry(id={self.id}, odentity={self.odentity}, food={self.food_name}, calories={self.calories})>"
