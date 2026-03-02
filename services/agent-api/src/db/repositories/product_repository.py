"""
Repository for custom_products table operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from decimal import Decimal

from ..models.custom_product import CustomProduct


class ProductRepository:
    """Repository for custom product CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(
        self,
        odentity: str,
        product_name: str,
        calories_per_100g: Decimal,
        brand_name: Optional[str] = None,
        protein_per_100g: Optional[Decimal] = None,
        carbs_per_100g: Optional[Decimal] = None,
        fat_per_100g: Optional[Decimal] = None,
        fiber_per_100g: Optional[Decimal] = None,
        sugar_per_100g: Optional[Decimal] = None,
        salt_per_100g: Optional[Decimal] = None,
        sodium_per_100g: Optional[Decimal] = None,
        ingredients: Optional[str] = None,
        allergens: Optional[str] = None,
        source: str = 'label_scan',
    ) -> CustomProduct:
        """
        Create a new custom product.

        Args:
            odentity: User identifier
            product_name: Product name
            calories_per_100g: Calories per 100g (required)
            ... other nutrition fields

        Returns:
            Created CustomProduct instance
        """
        product = CustomProduct(
            odentity=odentity,
            product_name=product_name,
            brand_name=brand_name,
            calories_per_100g=calories_per_100g,
            protein_per_100g=protein_per_100g,
            carbs_per_100g=carbs_per_100g,
            fat_per_100g=fat_per_100g,
            fiber_per_100g=fiber_per_100g,
            sugar_per_100g=sugar_per_100g,
            salt_per_100g=salt_per_100g,
            sodium_per_100g=sodium_per_100g,
            ingredients=ingredients,
            allergens=allergens,
            source=source,
        )

        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)

        return product

    async def get_product_by_id(
        self,
        product_id: int,
        odentity: str
    ) -> Optional[CustomProduct]:
        """
        Get product by ID for specific user.

        Args:
            product_id: Product ID
            odentity: User identifier

        Returns:
            CustomProduct or None if not found
        """
        stmt = select(CustomProduct).where(
            CustomProduct.id == product_id,
            CustomProduct.odentity == odentity,
            CustomProduct.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_product_nutrition(
        self,
        product_id: int,
        **updates
    ) -> Optional[CustomProduct]:
        """
        Update product nutrition values.

        Args:
            product_id: Product ID
            **updates: Fields to update (e.g., calories_per_100g=250)

        Returns:
            Updated product or None if not found
        """
        stmt = select(CustomProduct).where(CustomProduct.id == product_id)
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()

        if product:
            for key, value in updates.items():
                if hasattr(product, key):
                    setattr(product, key, value)

            await self.session.flush()
            await self.session.refresh(product)

        return product
