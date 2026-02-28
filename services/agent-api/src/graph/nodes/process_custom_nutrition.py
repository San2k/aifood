"""
LangGraph Node: process_custom_nutrition
Handles custom nutrition entries provided directly by user.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from ..state import NutritionBotState

logger = logging.getLogger(__name__)


def calculate_nutrition_from_100g(
    nutrition_per_100g: Dict[str, float],
    actual_weight_g: float
) -> Dict[str, float]:
    """
    Calculate nutrition values for actual weight from per-100g data.

    Args:
        nutrition_per_100g: Nutrition values per 100g
        actual_weight_g: Actual weight in grams

    Returns:
        Calculated nutrition values
    """
    multiplier = actual_weight_g / 100.0

    def safe_multiply(value, mult):
        """Multiply value by multiplier, handling None values."""
        if value is None:
            return None
        return round(value * mult, 1)

    return {
        "calories": safe_multiply(nutrition_per_100g.get("calories"), multiplier),
        "protein": safe_multiply(nutrition_per_100g.get("protein"), multiplier),
        "carbohydrate": safe_multiply(nutrition_per_100g.get("carbs"), multiplier),  # Note: use "carbohydrate" for DB
        "fat": safe_multiply(nutrition_per_100g.get("fat"), multiplier),
        "fiber": None,  # Not provided in custom input
        "sugar": None,
        "sodium": None
    }


async def process_custom_nutrition(state: NutritionBotState) -> Dict[str, Any]:
    """
    Process custom nutrition entries provided by user.

    Handles two cases:
    1. Direct nutrition for specific weight: "150g салат БЖУ 50/50/50 калорий 150"
       → Save immediately
    2. Nutrition per 100g: "Салат БЖУ 30/20/10 калорий 250 на 100г"
       → Ask for weight, then calculate and save

    Args:
        state: Current graph state

    Returns:
        State updates with pending entries or clarification requests
    """
    parsed_foods = state.get("parsed_foods", [])

    if not parsed_foods:
        logger.error("No parsed foods in state")
        return {
            "errors": state.get("errors", []) + ["No foods to process"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }

    # Process each food item with custom nutrition
    pending_entries = []
    clarification_requests = []

    for i, food_item in enumerate(parsed_foods):
        custom_nutrition = food_item.get("custom_nutrition")

        if not custom_nutrition:
            # Not a custom entry, should be handled by FatSecret search
            logger.warning(f"Food item {i} has no custom nutrition, skipping")
            continue

        food_name = food_item.get("name", "Unknown food")
        quantity = food_item.get("quantity")
        unit = food_item.get("unit", "g")
        is_per_100g = custom_nutrition.get("is_per_100g", False)

        logger.info(f"Processing custom nutrition for '{food_name}': is_per_100g={is_per_100g}, quantity={quantity}")

        # Case 1: Nutrition per 100g - need to ask for weight and calculate
        if is_per_100g:
            if not quantity:
                # Need clarification: ask for weight
                clarification_requests.append({
                    "type": "weight_for_100g",
                    "question": f"Сколько грамм '{food_name}' вы съели?",
                    "options": None,
                    "context": {
                        "food_index": i,
                        "food_name": food_name,
                        "nutrition_per_100g": custom_nutrition,
                        "unit": unit
                    }
                })
                logger.info(f"Added clarification request for weight of '{food_name}'")
            else:
                # Have weight, calculate nutrition
                calculated_nutrition = calculate_nutrition_from_100g(custom_nutrition, quantity)

                pending_entries.append({
                    "food_id": None,
                    "food_name": food_name,
                    "brand_name": None,
                    "serving_id": None,
                    "serving_description": f"{quantity}{unit}",
                    "serving_amount": quantity,
                    "serving_unit": unit,
                    "number_of_servings": 1.0,
                    "nutrition": calculated_nutrition,
                    "meal_type": None,
                    "is_custom": True
                })
                logger.info(f"Created pending entry for '{food_name}' with calculated nutrition from 100g")

        # Case 2: Direct nutrition for specific portion - save immediately
        else:
            if not quantity:
                # Need clarification: ask for weight
                clarification_requests.append({
                    "type": "weight",
                    "question": f"Сколько грамм '{food_name}' вы съели?",
                    "options": None,
                    "context": {
                        "food_index": i,
                        "food_name": food_name,
                        "custom_nutrition": custom_nutrition,
                        "unit": unit
                    }
                })
                logger.info(f"Added clarification request for weight of '{food_name}'")
            else:
                # Have all data, create entry directly
                nutrition = {
                    "calories": custom_nutrition.get("calories", 0),
                    "protein": custom_nutrition.get("protein"),
                    "carbohydrate": custom_nutrition.get("carbs"),  # Note: use "carbohydrate" for DB
                    "fat": custom_nutrition.get("fat"),
                    "fiber": None,
                    "sugar": None,
                    "sodium": None
                }

                pending_entries.append({
                    "food_id": None,
                    "food_name": food_name,
                    "brand_name": None,
                    "serving_id": None,
                    "serving_description": f"{quantity}{unit}",
                    "serving_amount": quantity,
                    "serving_unit": unit,
                    "number_of_servings": 1.0,
                    "nutrition": nutrition,
                    "meal_type": None,
                    "is_custom": True
                })
                logger.info(f"Created pending entry for '{food_name}' with direct custom nutrition")

    # Determine next step
    if clarification_requests:
        # Need clarification - ask user for missing info
        return {
            "clarification_requests": clarification_requests,
            "needs_clarification": True,
            "next_node": "need_clarification",
            "updated_at": datetime.utcnow()
        }
    elif pending_entries:
        # Have all data - save entries
        return {
            "pending_entries": pending_entries,
            "needs_clarification": False,
            "next_node": "save_entry",
            "updated_at": datetime.utcnow()
        }
    else:
        # No entries created
        logger.error("No custom entries or clarifications generated")
        return {
            "errors": state.get("errors", []) + ["Failed to process custom nutrition"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
