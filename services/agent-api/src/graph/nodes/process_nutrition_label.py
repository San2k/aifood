"""
LangGraph Node: process_nutrition_label
Processes nutrition label photos using Vision AI to extract product info and KBJU.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def process_nutrition_label(state: NutritionBotState) -> Dict[str, Any]:
    """
    Process nutrition label photo to extract product info and KBJU.

    Priority 1: Try to find product in FatSecret by name/brand
    Priority 2: If not found, use OCR KBJU data as custom nutrition

    Args:
        state: Current graph state

    Returns:
        State updates with label data or search query
    """
    photo_url = state.get("photo_file_id")

    if not photo_url:
        logger.error("No photo URL provided")
        return {
            "errors": state.get("errors", []) + ["No photo provided"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }

    logger.info(f"Processing nutrition label photo: {photo_url[:50]}...")

    try:
        # Use Vision LLM to extract nutrition label data
        label_result = await llm_service.parse_nutrition_label(
            image_url=photo_url
        )

        # Check if parsing succeeded
        if "error" in label_result:
            logger.error(f"Label parsing failed: {label_result.get('error')}")
            return {
                "errors": state.get("errors", []) + [f"Failed to read label: {label_result.get('error')}"],
                "should_end": True,
                "updated_at": datetime.utcnow()
            }

        product_name = label_result.get("product_name")
        brand = label_result.get("brand")
        # Support both new format (nutrition_values) and old format (nutrition_per_100g)
        nutrition_values = label_result.get("nutrition_values") or label_result.get("nutrition_per_100g", {})
        nutrition_per_serving_weight = label_result.get("nutrition_per_serving_weight", 100)
        serving_size = label_result.get("serving_size")
        confidence = label_result.get("confidence", 0.0)

        logger.info(f"Extracted from label: {product_name} ({brand}), confidence: {confidence}")
        logger.info(f"Nutrition values for {nutrition_per_serving_weight}g: {nutrition_values}")

        # Convert nutrition values to per-100g if needed
        def convert_to_per_100g(values: Dict[str, float], current_weight: float) -> Dict[str, float]:
            """Convert nutrition values from any weight to per-100g."""
            if current_weight == 100:
                return values  # Already per 100g

            multiplier = 100.0 / current_weight
            return {
                "calories": round(values.get("calories", 0) * multiplier, 1) if values.get("calories") is not None else None,
                "protein": round(values.get("protein", 0) * multiplier, 1) if values.get("protein") is not None else None,
                "carbs": round(values.get("carbs", 0) * multiplier, 1) if values.get("carbs") is not None else None,
                "fat": round(values.get("fat", 0) * multiplier, 1) if values.get("fat") is not None else None,
                "fiber": round(values.get("fiber", 0) * multiplier, 1) if values.get("fiber") is not None else None,
                "sugar": round(values.get("sugar", 0) * multiplier, 1) if values.get("sugar") is not None else None,
                "sodium": round(values.get("sodium", 0) * multiplier, 1) if values.get("sodium") is not None else None,
            }

        nutrition_per_100g = convert_to_per_100g(nutrition_values, nutrition_per_serving_weight)
        logger.info(f"Converted to per-100g: {nutrition_per_100g}")

        # Priority 1: Try FatSecret search if we have product name
        if product_name and confidence >= 0.6:
            # Create search query
            search_query = product_name
            if brand:
                search_query = f"{product_name} {brand}"

            logger.info(f"Attempting FatSecret search for: {search_query}")

            # Store OCR data as fallback
            ocr_fallback = {
                "product_name": product_name,
                "brand": brand,
                "nutrition_per_100g": nutrition_per_100g,
                "serving_size": serving_size,
                "confidence": confidence
            }

            # Create parsed food item for FatSecret search
            # Store OCR nutrition as custom_nutrition in case FatSecret fails
            parsed_food = {
                "name": search_query,
                "quantity": None,
                "unit": "g",
                "cooking_method": None,
                "notes": "From nutrition label",
                "custom_nutrition": None  # Will use if FatSecret search returns no results
            }

            # Add OCR nutrition data if available for fallback
            if nutrition_per_100g and nutrition_per_100g.get("calories"):
                parsed_food["ocr_nutrition_fallback"] = {
                    "calories": nutrition_per_100g.get("calories"),
                    "protein": nutrition_per_100g.get("protein"),
                    "carbs": nutrition_per_100g.get("carbs"),
                    "fat": nutrition_per_100g.get("fat"),
                    "is_per_100g": True  # Labels usually show per 100g
                }

            return {
                "parsed_foods": [parsed_food],
                "ocr_label_data": ocr_fallback,
                "next_node": "fatsecret_search",
                "updated_at": datetime.utcnow()
            }

        # Priority 2: Use OCR KBJU if no confident product name or low confidence
        else:
            logger.info("No confident product name, using OCR nutrition data as custom entry")

            if not nutrition_per_100g or not nutrition_per_100g.get("calories"):
                return {
                    "errors": state.get("errors", []) + ["Could not read nutrition data from label"],
                    "should_end": True,
                    "updated_at": datetime.utcnow()
                }

            # Create custom nutrition entry
            food_name = product_name or "Продукт с этикетки"

            parsed_food = {
                "name": food_name,
                "quantity": None,  # Will ask user
                "unit": "g",
                "cooking_method": None,
                "notes": f"From label (OCR confidence: {confidence:.0%})",
                "custom_nutrition": {
                    "calories": nutrition_per_100g.get("calories"),
                    "protein": nutrition_per_100g.get("protein"),
                    "carbs": nutrition_per_100g.get("carbs"),
                    "fat": nutrition_per_100g.get("fat"),
                    "is_per_100g": True  # Assume per 100g unless specified otherwise
                }
            }

            return {
                "parsed_foods": [parsed_food],
                "has_custom_nutrition": True,
                "next_node": "process_custom_nutrition",
                "updated_at": datetime.utcnow()
            }

    except Exception as e:
        logger.error(f"Error processing nutrition label: {e}", exc_info=True)
        return {
            "errors": state.get("errors", []) + [f"Label processing error: {str(e)}"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
