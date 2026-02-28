"""
LangGraph Node: process_photo
Processes food package photos using Vision AI to extract product name.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def process_photo(state: NutritionBotState) -> Dict[str, Any]:
    """
    Process photo to determine type and route accordingly.

    Photo types:
    1. Nutrition label (with KBJU) → process_nutrition_label
    2. Food package (product name only) → search FatSecret by name

    Args:
        state: Current graph state

    Returns:
        State updates with routing decision
    """
    photo_url = state.get("photo_file_id")  # This will be Telegram file URL

    if not photo_url:
        logger.error("No photo URL provided")
        return {
            "errors": state.get("errors", []) + ["No photo provided"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }

    logger.info(f"Processing food photo: {photo_url[:50]}...")

    try:
        # First, try to parse as nutrition label (has KBJU data)
        # This is done first because labels contain more useful data
        label_result = await llm_service.parse_nutrition_label(
            image_url=photo_url
        )

        # Check if this is a nutrition label with KBJU data
        # Support both new format (nutrition_values) and old format (nutrition_per_100g)
        nutrition_data = label_result.get("nutrition_values") or label_result.get("nutrition_per_100g", {})
        has_nutrition_data = (
            nutrition_data.get("calories") is not None or
            nutrition_data.get("protein") is not None or
            nutrition_data.get("fat") is not None
        )

        if has_nutrition_data and not label_result.get("error"):
            logger.info("Detected nutrition label with KBJU data - routing to process_nutrition_label")
            # Route to nutrition label processing
            return {
                "next_node": "process_nutrition_label",
                "updated_at": datetime.utcnow()
            }

        # If no nutrition data, try to recognize as product package
        logger.info("No nutrition data found, trying product recognition")
        recognition_result = await llm_service.recognize_food_from_photo(
            image_url=photo_url
        )

        # Check if recognition succeeded
        if "error" in recognition_result or not recognition_result.get("product_name"):
            logger.warning("Vision API failed to recognize product")
            return {
                "errors": state.get("errors", []) + ["Could not recognize product from photo. Please try text input."],
                "should_end": True,
                "updated_at": datetime.utcnow()
            }

        product_name = recognition_result.get("product_name")
        search_query = recognition_result.get("search_query") or product_name
        brand = recognition_result.get("brand")
        confidence = recognition_result.get("confidence", 0.0)

        logger.info(f"Recognized: {product_name} (brand: {brand}, confidence: {confidence})")

        # Store as parsed food for searching
        parsed_foods = [{
            "name": search_query,
            "quantity": None,  # Will ask for quantity later if needed
            "unit": None,
            "cooking_method": None,
            "notes": f"From photo: {product_name}" + (f" ({brand})" if brand else "")
        }]

        # If confidence is low, ask user to confirm
        if confidence < 0.6:
            return {
                "parsed_foods": parsed_foods,
                "clarification_requests": [{
                    "type": "confirmation",
                    "question": f"Распознал: {product_name}\nЭто правильно?",
                    "options": ["Да, правильно", "Нет, переввести"],
                    "context": {
                        "product_name": product_name,
                        "search_query": search_query,
                        "confidence": confidence
                    }
                }],
                "needs_clarification": True,
                "next_node": "need_clarification",
                "updated_at": datetime.utcnow()
            }

        # High confidence - proceed to search
        return {
            "parsed_foods": parsed_foods,
            "needs_clarification": False,
            "next_node": "fatsecret_search",
            "updated_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        return {
            "errors": state.get("errors", []) + [f"Photo processing error: {str(e)}"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
