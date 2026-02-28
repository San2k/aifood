"""
LangGraph Node: calculate_totals
Calculates daily nutrition totals.
"""

import logging
from typing import Dict, Any
from datetime import datetime, date

from ..state import NutritionBotState
from ...db.session import AsyncSessionLocal
from ...db.repositories.food_log_repository import FoodLogRepository

logger = logging.getLogger(__name__)


async def calculate_totals(state: NutritionBotState) -> Dict[str, Any]:
    """
    Calculate daily nutrition totals for the user.
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with daily totals
    """
    user_id = state.get("user_id")
    
    if not user_id:
        logger.error("No user_id in state")
        return {
            "errors": state.get("errors", []) + ["No user_id"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    logger.info(f"Calculating daily totals for user {user_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            repo = FoodLogRepository(session)
            
            # Calculate totals for today
            today = date.today()
            totals = await repo.calculate_daily_totals(user_id, today)
            
            logger.info(f"Daily totals: {totals['calories']} kcal, {totals['protein']}g protein")
            
            return {
                "daily_totals": totals,
                "next_node": "generate_advice",
                "updated_at": datetime.utcnow()
            }
    
    except Exception as e:
        logger.error(f"Error calculating totals: {e}")
        return {
            "errors": state.get("errors", []) + [f"Calculation error: {str(e)}"],
            "daily_totals": None,
            "next_node": "generate_advice",  # Continue anyway
            "updated_at": datetime.utcnow()
        }
