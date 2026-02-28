"""
LangGraph Node: save_entry
Saves food log entry to database.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...db.session import AsyncSessionLocal
from ...db.repositories.food_log_repository import FoodLogRepository

logger = logging.getLogger(__name__)


async def save_entry(state: NutritionBotState) -> Dict[str, Any]:
    """
    Save pending food entry to database.
    
    Steps:
    1. Get pending entry from state
    2. Create food_log_entry in database
    3. Store entry ID in saved_entry_ids
    4. Proceed to calculate_totals
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with saved entry ID
    """
    pending_entries = state.get("pending_entries", [])
    raw_input = state.get("raw_input", "")
    user_id = state.get("user_id")
    
    if not pending_entries:
        logger.error("No pending entries to save")
        return {
            "errors": state.get("errors", []) + ["No entries to save"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    if not user_id:
        logger.error("No user_id in state")
        return {
            "errors": state.get("errors", []) + ["No user_id"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    # Get first pending entry (simplified - handle one at a time)
    entry_data = pending_entries[0]
    
    logger.info(f"Saving food entry for user {user_id}: {entry_data.get('food_name')}")
    
    try:
        # Create database session and repository
        async with AsyncSessionLocal() as session:
            repo = FoodLogRepository(session)
            
            # Extract nutrition data
            nutrition = entry_data.get("nutrition", {})
            
            # Create entry
            entry = await repo.create_entry(
                user_id=user_id,
                food_id=entry_data.get("food_id"),
                food_name=entry_data.get("food_name"),
                brand_name=entry_data.get("brand_name"),
                serving_id=entry_data.get("serving_id"),
                serving_description=entry_data.get("serving_description"),
                serving_size=entry_data.get("serving_amount"),
                serving_unit=entry_data.get("serving_unit"),
                number_of_servings=entry_data.get("number_of_servings", 1.0),
                calories=nutrition.get("calories", 0),
                protein=nutrition.get("protein"),
                carbohydrates=nutrition.get("carbohydrate"),  # Note: FatSecret uses "carbohydrate"
                fat=nutrition.get("fat"),
                fiber=nutrition.get("fiber"),
                sugar=nutrition.get("sugar"),
                sodium=nutrition.get("sodium"),
                meal_type=entry_data.get("meal_type"),
                consumed_at=datetime.utcnow(),  # TODO: Allow user to specify time
                input_type="text",  # TODO: Get from state.input_type
                original_input=raw_input,
                is_custom=entry_data.get("is_custom", False)
            )
            
            await session.commit()
            
            logger.info(f"Saved entry ID: {entry.id}, calories: {entry.calories}")
            
            return {
                "saved_entry_ids": [entry.id],
                "next_node": "calculate_totals",
                "updated_at": datetime.utcnow()
            }
    
    except Exception as e:
        logger.error(f"Error saving entry: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Database error: {str(e)}"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
