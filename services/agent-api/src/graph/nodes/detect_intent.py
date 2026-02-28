"""
LangGraph Node: detect_intent
Detects user intent to route conversation appropriately.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def detect_intent(state: NutritionBotState) -> Dict[str, Any]:
    """
    Detect user intent from natural language input.

    Routes to appropriate handler based on intent:
    - food_entry: Parse and log food
    - view_report: Show daily/weekly report
    - question: Answer nutrition question
    - chat: Friendly conversational response

    Args:
        state: Current graph state

    Returns:
        State updates with detected intent and routing decision
    """
    raw_input = state.get("raw_input", "")

    logger.info(f"Detecting intent for: {raw_input[:50]}...")

    try:
        # Detect intent using LLM
        intent_result = await llm_service.detect_intent(raw_input)

        detected_intent = intent_result.get("intent", "food_entry")
        confidence = intent_result.get("confidence", 0.5)
        reasoning = intent_result.get("reasoning", "")

        logger.info(f"Detected intent: {detected_intent} (confidence: {confidence})")
        logger.info(f"Reasoning: {reasoning}")

        # Determine next node based on intent
        if detected_intent == "food_entry":
            next_node = "normalize_input"

        elif detected_intent == "view_report":
            next_node = "conversational_response"

        elif detected_intent == "question":
            next_node = "conversational_response"

        elif detected_intent == "chat":
            next_node = "conversational_response"

        else:
            # Default to food entry if unclear
            logger.warning(f"Unknown intent: {detected_intent}, defaulting to food_entry")
            detected_intent = "food_entry"
            next_node = "normalize_input"

        return {
            "input_type": "text",
            "detected_intent": detected_intent,
            "intent_confidence": confidence,
            "next_node": next_node,
            "updated_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error detecting intent: {e}", exc_info=True)
        # Default to food entry on error
        return {
            "input_type": "text",
            "detected_intent": "food_entry",
            "intent_confidence": 0.5,
            "next_node": "normalize_input",
            "errors": state.get("errors", []) + [f"Intent detection error: {str(e)}"],
            "updated_at": datetime.utcnow()
        }
