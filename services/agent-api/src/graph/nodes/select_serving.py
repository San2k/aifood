"""
LangGraph Node: select_serving
Selects appropriate serving based on user input and FatSecret data.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services import mcp_client

logger = logging.getLogger(__name__)


async def select_serving(state: NutritionBotState) -> Dict[str, Any]:
    """
    Select serving option for the food.
    
    Process:
    1. Get servings from FatSecret
    2. Match to user's quantity (e.g., "150g" → find 100g serving and calculate)
    3. If ambiguous → ask user to select
    4. Build pending_food_entry with nutrition data
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with selected serving and nutrition
    """
    selected_food = state.get("selected_food")
    parsed_foods = state.get("parsed_foods", [])
    
    if not selected_food:
        logger.error("No selected food")
        return {
            "errors": state.get("errors", []) + ["No food selected"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    food_id = selected_food.get("food_id")
    food_name = selected_food.get("food_name")
    brand_name = selected_food.get("brand_name")
    
    logger.info(f"Selecting serving for food: {food_name} (ID: {food_id})")
    
    try:
        # Get servings from FatSecret
        servings = await mcp_client.get_servings(food_id)
        
        if not servings:
            logger.error(f"No servings found for food {food_id}")
            return {
                "errors": state.get("errors", []) + ["No serving data available"],
                "should_end": True,
                "updated_at": datetime.utcnow()
            }
        
        # Get user's desired quantity from parsed food
        parsed_food = parsed_foods[0] if parsed_foods else {}
        user_quantity = parsed_food.get("quantity")
        user_unit = parsed_food.get("unit", "g")
        
        logger.info(f"User quantity: {user_quantity} {user_unit}, Available servings: {len(servings)}")
        
        # Try to find matching serving
        best_serving = None
        number_of_servings = 1.0
        
        # Strategy 1: Find 100g serving (most common)
        for serving in servings:
            metric_amount = serving.get("metric_serving_amount")
            metric_unit = serving.get("metric_serving_unit")
            
            if metric_amount == 100.0 and metric_unit == "g" and user_unit == "g":
                best_serving = serving
                if user_quantity:
                    number_of_servings = user_quantity / 100.0
                logger.info(f"Found 100g serving, calculated servings: {number_of_servings}")
                break
        
        # Strategy 2: Find serving that matches user's amount
        if not best_serving and user_quantity:
            for serving in servings:
                metric_amount = serving.get("metric_serving_amount")
                if metric_amount and abs(metric_amount - user_quantity) < 1.0:
                    best_serving = serving
                    number_of_servings = 1.0
                    logger.info(f"Found exact match serving: {metric_amount}g")
                    break
        
        # Strategy 3: Use first serving as fallback
        if not best_serving:
            best_serving = servings[0]
            logger.info(f"Using first serving as fallback: {best_serving.get('serving_description')}")
        
        # Extract nutrition from serving (nutrition is directly in serving dict)
        nutrient_keys = [
            "calories", "protein", "carbohydrate", "fat",
            "saturated_fat", "polyunsaturated_fat", "monounsaturated_fat",
            "cholesterol", "sodium", "potassium", "fiber", "sugar"
        ]

        # Calculate final nutrition (serving nutrition * number_of_servings)
        final_nutrition = {}
        for key in nutrient_keys:
            value = best_serving.get(key, 0)
            if value is not None:
                final_nutrition[key] = float(value) * number_of_servings
        
        # Build pending food entry
        pending_entry = {
            "food_id": food_id,
            "food_name": food_name,
            "brand_name": brand_name,
            "serving_id": best_serving.get("serving_id"),
            "serving_description": best_serving.get("serving_description"),
            "serving_amount": best_serving.get("metric_serving_amount"),
            "serving_unit": best_serving.get("metric_serving_unit", "g"),
            "number_of_servings": number_of_servings,
            "nutrition": final_nutrition,
            "meal_type": None,  # Will be set later or default to "snack"
            "is_custom": False
        }
        
        logger.info(f"Created pending entry: {food_name}, {final_nutrition.get('calories', 0)} kcal")
        
        return {
            "selected_serving": best_serving,
            "pending_entries": [pending_entry],
            "next_node": "save_entry",
            "updated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error selecting serving: {e}")
        return {
            "errors": state.get("errors", []) + [f"Serving selection error: {str(e)}"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
