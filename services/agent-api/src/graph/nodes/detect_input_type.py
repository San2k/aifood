"""
LangGraph Node: detect_input_type
Determines the type of user input and routes accordingly.
"""

import logging
from typing import Dict, Any
import re

from ..state import NutritionBotState

logger = logging.getLogger(__name__)


def is_new_food_request(raw_input: str, input_type: str) -> bool:
    """
    Determine if this is a new food entry request vs. a response to clarification.

    Args:
        raw_input: User's text input
        input_type: Type of input (text, callback, etc.)

    Returns:
        True if this is a new food request
    """
    if input_type != "text":
        return False

    if not raw_input:
        return False

    text_lower = raw_input.lower()

    # Check for explicit food entry keywords
    food_entry_keywords = [
        r'^съел\s', r'^ел\s', r'^ate\s', r'^had\s', r'^eating\s',
        r'кбжу\s*\d', r'бжу\s*\d', r'калорий\s*\d',
        r'\d+\s*г\s+\w+', r'\d+\s*грамм', r'\d+g\s+\w+'
    ]

    for pattern in food_entry_keywords:
        if re.search(pattern, text_lower):
            logger.info(f"Detected new food request via pattern: {pattern}")
            return True

    return False


async def detect_input_type(state: NutritionBotState) -> Dict[str, Any]:
    """
    Detect input type and set routing.

    Routes:
    - "text" → detect_intent (for conversational AI)
    - "photo" → process_photo
    - "callback"/"confirmation" → handle as continuation of existing flow
    - If next_node already set (from loaded state) → use that UNLESS it's a new food request

    Args:
        state: Current graph state

    Returns:
        State updates
    """
    input_type = state.get("input_type", "text")
    raw_input = state.get("raw_input", "")

    # Check if this is a NEW food request (overrides saved state)
    if is_new_food_request(raw_input, input_type):
        logger.info("Detected new food request - resetting conversation state")
        return {
            "next_node": "detect_intent",
            "clarification_requests": [],
            "clarification_responses": {},
            "needs_clarification": False,
            "food_candidates": [],
            "food_selection_page": 0,
            "parsed_foods": [],
            "updated_at": state.get("created_at")
        }

    # Check if we're resuming with a pre-set next_node
    if state.get("next_node"):
        logger.info(f"Using pre-set next_node: {state.get('next_node')}")
        return {
            "updated_at": state.get("created_at")
        }
    
    logger.info(f"Detected input type: {input_type}")
    
    updates = {
        "updated_at": state.get("created_at")
    }
    
    # Set routing based on input type
    if input_type == "photo":
        updates["next_node"] = "process_photo"
    elif input_type in ["callback", "confirmation"]:
        # For callbacks/confirmations, check if we have pending clarifications
        if state.get("clarification_requests"):
            updates["next_node"] = "need_clarification"
        else:
            updates["next_node"] = "fatsecret_search"
    else:  # text input
        # Route text to intent detection first (for conversational AI)
        updates["next_node"] = "detect_intent"
    
    return updates
