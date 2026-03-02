"""
SQLAlchemy model for custom_products table.
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Text, Boolean, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from ..session import Base


class CustomProduct(Base):
    """User-created product from nutrition label scan."""

    __tablename__ = 'custom_products'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    odentity = Column(String(255), nullable=False, index=True)
    product_name = Column(String(500), nullable=False)
    brand_name = Column(String(255))
    barcode = Column(String(100))

    # Nutrition per 100g (always normalized)
    calories_per_100g = Column(Numeric(10, 2), nullable=False)
    protein_per_100g = Column(Numeric(10, 2))
    carbs_per_100g = Column(Numeric(10, 2))
    fat_per_100g = Column(Numeric(10, 2))
    fiber_per_100g = Column(Numeric(10, 2))
    sugar_per_100g = Column(Numeric(10, 2))
    salt_per_100g = Column(Numeric(10, 2))
    sodium_per_100g = Column(Numeric(10, 2))

    # Additional data
    ingredients = Column(Text)
    allergens = Column(Text)

    # Metadata
    source = Column(String(50), nullable=False, default='label_scan')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint('calories_per_100g >= 0 AND calories_per_100g <= 900', name='check_calories_range'),
        CheckConstraint(
            'protein_per_100g IS NULL OR (protein_per_100g >= 0 AND protein_per_100g <= 100)',
            name='check_protein_range'
        ),
        CheckConstraint(
            'carbs_per_100g IS NULL OR (carbs_per_100g >= 0 AND carbs_per_100g <= 100)',
            name='check_carbs_range'
        ),
        CheckConstraint(
            'fat_per_100g IS NULL OR (fat_per_100g >= 0 AND fat_per_100g <= 100)',
            name='check_fat_range'
        ),
    )

    def __repr__(self):
        return f"<CustomProduct(id={self.id}, name='{self.product_name}', brand='{self.brand_name}')>"
