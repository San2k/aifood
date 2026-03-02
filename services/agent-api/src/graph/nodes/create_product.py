"""
Create custom product in database.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal
from ...db.repositories.product_repository import ProductRepository
from ...db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def create_product(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert custom product into custom_products table.

    Args:
        state: LabelProcessingState with product_name and nutrition_per_100g

    Returns:
        Updated state with product_id
    """
    scan_id = state["scan_id"]
    odentity = state["odentity"]

    logger.info(f"[{scan_id}] Creating custom product for {odentity}")

    try:
        async with AsyncSessionLocal() as session:
            repo = ProductRepository(session)

            # Prepare nutrition data
            nutrition = state["nutrition_per_100g"]

            product = await repo.create_product(
                odentity=odentity,
                product_name=state["product_name"],
                brand_name=state.get("brand"),
                calories_per_100g=Decimal(str(nutrition["calories_kcal"])),
                protein_per_100g=Decimal(str(nutrition.get("protein_g", 0))),
                carbs_per_100g=Decimal(str(nutrition.get("carbs_g", 0))),
                fat_per_100g=Decimal(str(nutrition.get("fat_g", 0))),
                fiber_per_100g=Decimal(str(nutrition.get("fiber_g", 0))) if nutrition.get("fiber_g") else None,
                sugar_per_100g=Decimal(str(nutrition.get("sugar_g", 0))) if nutrition.get("sugar_g") else None,
                salt_per_100g=Decimal(str(nutrition.get("salt_g", 0))) if nutrition.get("salt_g") else None,
                ingredients=state.get("ingredients"),
                allergens=state.get("allergens"),
            )

            await session.commit()

            logger.info(f"[{scan_id}] Created product ID={product.id}: {product.product_name}")

            return {
                **state,
                "product_id": product.id,
                "current_step": "create_product",
                "progress": 85,
                "updated_at": datetime.utcnow(),
            }

    except Exception as e:
        logger.error(f"[{scan_id}] Failed to create product: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Failed to create product: {str(e)}",
            "should_end": True,
        }
