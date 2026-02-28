"""
LangGraph Node: need_clarification
Checks if clarifications are needed and handles user responses.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState

logger = logging.getLogger(__name__)


async def need_clarification(state: NutritionBotState) -> Dict[str, Any]:
    """
    Check if clarifications are needed from the user.
    
    If clarifications exist and no responses yet → return to user (END)
    If clarifications exist with responses → process and continue
    If no clarifications → proceed to next step
    
    Args:
        state: Current graph state
        
    Returns:
        State updates
    """
    clarification_requests = state.get("clarification_requests", [])
    clarification_responses = state.get("clarification_responses", {})
    
    logger.info(f"Checking clarifications: {len(clarification_requests)} requests, {len(clarification_responses)} responses")
    
    # If we have clarification requests but no responses, wait for user
    if clarification_requests and not clarification_responses:
        logger.info("Waiting for user clarification")
        return {
            "needs_clarification": True,
            "should_end": True,  # End graph execution, wait for user input
            "updated_at": datetime.utcnow()
        }
    
    # If we have responses, process them
    if clarification_requests and clarification_responses:
        logger.info("Processing clarification responses")
        
        # Apply responses to parsed foods
        parsed_foods = state.get("parsed_foods", [])
        
        for clarif in clarification_requests:
            clarif_type = clarif.get("type")
            context = clarif.get("context", {})
            food_index = context.get("food_index", 0)
            
            if food_index < len(parsed_foods):
                food_item = parsed_foods[food_index]
                response_key = f"clarif_{food_index}"
                
                if response_key in clarification_responses:
                    response = clarification_responses[response_key]

                    # Apply response based on type
                    if clarif_type == "weight":
                        # Parse weight from response (e.g., "150", "150g", "150 грамм")
                        weight_str = ''.join(filter(str.isdigit, str(response)))
                        if weight_str:
                            food_item["quantity"] = float(weight_str)
                            food_item["unit"] = "g"

                            # If this food has custom nutrition, return to process_custom_nutrition
                            if food_item.get("custom_nutrition"):
                                logger.info(f"Updated weight for custom nutrition item, returning to process_custom_nutrition")
                                return {
                                    "parsed_foods": parsed_foods,
                                    "clarification_requests": [],
                                    "needs_clarification": False,
                                    "next_node": "process_custom_nutrition",
                                    "updated_at": datetime.utcnow()
                                }

                    elif clarif_type == "weight_for_100g":
                        # Weight for per-100g custom nutrition
                        # Parse weight and update food item, then go back to process_custom_nutrition
                        weight_str = ''.join(filter(str.isdigit, str(response)))
                        if weight_str:
                            food_item["quantity"] = float(weight_str)
                            food_item["unit"] = "g"
                            logger.info(f"Updated weight for per-100g nutrition: {weight_str}g")
                            # Return to process_custom_nutrition to calculate
                            return {
                                "parsed_foods": parsed_foods,
                                "clarification_requests": [],
                                "needs_clarification": False,
                                "next_node": "process_custom_nutrition",
                                "updated_at": datetime.utcnow()
                            }

                    elif clarif_type == "cooking_method":
                        food_item["cooking_method"] = response

                    elif clarif_type == "food_selection":
                        # User selected a food from the list
                        # Response is the option text, e.g. "Apple, raw (Generic)"
                        food_candidates = state.get("food_candidates", [])
                        options = clarif.get("options", [])
                        current_page = state.get("food_selection_page", 0)

                        # Check for special options first
                        if response == "🔍 Другой вариант":
                            # User wants to see more options
                            logger.info("User requested more food options")
                            # Go back to fatsecret_search to show next page
                            return {
                                "food_selection_page": current_page + 1,
                                "clarification_requests": [],
                                "needs_clarification": False,
                                "next_node": "show_more_foods",
                                "updated_at": datetime.utcnow()
                            }

                        if response == "◀️ Предыдущие":
                            # User wants to see previous options
                            logger.info("User requested previous food options")
                            return {
                                "food_selection_page": max(0, current_page - 1),
                                "clarification_requests": [],
                                "needs_clarification": False,
                                "next_node": "show_more_foods",
                                "updated_at": datetime.utcnow()
                            }

                        if response == "📋 Использовать данные с этикетки":
                            # User wants to use OCR nutrition data from label
                            logger.info("User chose to use nutrition data from label")
                            # Get OCR fallback data from parsed foods
                            parsed_foods = state.get("parsed_foods", [])
                            if parsed_foods and parsed_foods[0].get("ocr_nutrition_fallback"):
                                ocr_data = parsed_foods[0]["ocr_nutrition_fallback"]
                                parsed_foods[0]["custom_nutrition"] = ocr_data
                                return {
                                    "parsed_foods": parsed_foods,
                                    "clarification_requests": [],
                                    "clarification_responses": {},  # Clear old responses
                                    "food_candidates": [],  # Clear FatSecret results
                                    "food_selection_page": 0,  # Reset pagination
                                    "needs_clarification": False,
                                    "next_node": "process_custom_nutrition",
                                    "updated_at": datetime.utcnow()
                                }

                        if response == "➕ Создать свой продукт":
                            # User wants to create custom food
                            logger.info("User wants to create custom food")
                            return {
                                "clarification_requests": [],
                                "needs_clarification": False,
                                "next_node": "create_custom_food",
                                "updated_at": datetime.utcnow()
                            }

                        # Find which option was selected
                        try:
                            selected_index = options.index(response)
                            # Account for pagination offset
                            actual_index = current_page * 5 + selected_index

                            if actual_index < len(food_candidates):
                                # Store selected food
                                selected_food = food_candidates[actual_index]
                                logger.info(f"User selected food: {selected_food.get('food_name')}")

                                # Return early with selected food, skip further clarification processing
                                return {
                                    "selected_food": selected_food,
                                    "clarification_requests": [],
                                    "needs_clarification": False,
                                    "food_selection_page": 0,  # Reset page
                                    "next_node": "select_serving",
                                    "updated_at": datetime.utcnow()
                                }
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Could not match food selection: {response}")
        
        # Clear clarifications and proceed
        return {
            "parsed_foods": parsed_foods,
            "clarification_requests": [],
            "needs_clarification": False,
            "next_node": "fatsecret_search",
            "updated_at": datetime.utcnow()
        }
    
    # No clarifications needed, proceed
    logger.info("No clarifications needed")
    return {
        "needs_clarification": False,
        "next_node": "fatsecret_search",
        "updated_at": datetime.utcnow()
    }
