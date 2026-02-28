"""
LangGraph Node: generate_advice
Generates personalized nutrition advice using AI.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services import openai_service

logger = logging.getLogger(__name__)


async def generate_advice(state: NutritionBotState) -> Dict[str, Any]:
    """
    Generate AI-powered nutrition advice based on daily totals and user goals.
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with AI advice
    """
    daily_totals = state.get("daily_totals", {})
    user_id = state.get("user_id")
    
    logger.info(f"Generating advice for user {user_id}")
    
    # Build user context (simplified - in production would fetch from user_profile)
    user_context = {
        "goal": "maintenance",
        "target_calories": 2000,
        "target_protein": 100
    }
    
    # Recent entries (simplified)
    recent_entries = []
    
    try:
        advice = await openai_service.generate_advice(
            user_context=user_context,
            daily_totals=daily_totals,
            recent_entries=recent_entries
        )
        
        logger.info(f"Generated advice: {advice[:50]}...")
        
        return {
            "ai_advice": advice,
            "should_end": True,  # End graph execution
            "updated_at": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        return {
            "ai_advice": "Отличная работа! Продолжайте следить за питанием.",
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
