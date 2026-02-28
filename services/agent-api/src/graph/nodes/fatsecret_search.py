"""
LangGraph Node: fatsecret_search
Searches for foods in FatSecret database.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState
from ...services import mcp_client
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def fatsecret_search(state: NutritionBotState) -> Dict[str, Any]:
    """
    Search for foods in FatSecret database based on parsed food items.
    
    For each parsed food item:
    1. Search FatSecret
    2. Store candidates
    3. If single match → auto-select
    4. If multiple matches → request user selection
    5. If no matches → suggest custom food or rephrase
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with search results
    """
    parsed_foods = state.get("parsed_foods", [])
    
    if not parsed_foods:
        logger.warning("No parsed foods to search")
        return {
            "errors": state.get("errors", []) + ["No foods to search"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    logger.info(f"Searching FatSecret for {len(parsed_foods)} foods")
    
    all_candidates = []
    needs_user_selection = False
    
    try:
        # Search for first food item (simplified - handle one at a time)
        food_item = parsed_foods[0]
        food_name = food_item.get("name", "")
        cooking_method = food_item.get("cooking_method", "")

        # Translate food name to English for FatSecret API (supports only English in free tier)
        logger.info(f"Original food name: {food_name}")
        food_name_en = await llm_service.translate_to_english(food_name)
        logger.info(f"Translated to English: {food_name_en}")

        # Build search query
        search_query = food_name_en
        if cooking_method:
            # Also translate cooking method if present
            cooking_method_en = await llm_service.translate_to_english(cooking_method)
            search_query += f" {cooking_method_en}"

        logger.info(f"Searching FatSecret for: {search_query}")

        # Perform search with fallback strategies
        candidates = await mcp_client.search_foods(search_query, max_results=10)

        # If no results, try broader search with just the main word
        if not candidates and len(food_name_en.split()) > 1:
            # Try searching for just the main noun
            main_word = food_name_en.split()[-1]
            logger.info(f"No results for '{search_query}', trying broader search: {main_word}")
            candidates = await mcp_client.search_foods(main_word, max_results=10)

        if not candidates:
            logger.warning(f"No results found for: {search_query}")

            # Check if we have OCR nutrition data as fallback (from nutrition label)
            ocr_fallback = food_item.get("ocr_nutrition_fallback")
            if ocr_fallback:
                logger.info("No FatSecret matches, using OCR nutrition data from label")
                # Use OCR nutrition data as custom nutrition
                parsed_foods[i]["custom_nutrition"] = ocr_fallback
                return {
                    "parsed_foods": parsed_foods,
                    "has_custom_nutrition": True,
                    "next_node": "process_custom_nutrition",
                    "updated_at": datetime.utcnow()
                }

            # No matches and no OCR fallback - offer to rephrase or create custom
            return {
                "food_candidates": [],
                "clarification_requests": [{
                    "type": "food_selection",
                    "question": f"Не нашел '{food_name}' в базе.\n\nПопробуйте:\n1. Переформулировать запрос\n2. Создать свой продукт",
                    "options": ["Переформулировать", "Создать свой продукт"],
                    "context": {"food_name": food_name}
                }],
                "needs_clarification": True,
                "should_end": True,
                "updated_at": datetime.utcnow()
            }
        
        all_candidates = candidates

        # Always show results to user for selection (even if 1 result)
        # This gives them confidence and control
        logger.info(f"Found {len(candidates)} matches, requesting user selection")

        # Limit to top 5 most relevant
        top_candidates = candidates[:5]

        options = []
        for c in top_candidates:
            brand = c.get('brand_name', 'Generic')
            # Clean up the food name for display
            name = c.get('food_name', '')
            if brand and brand.lower() != 'generic':
                options.append(f"{name} ({brand})")
            else:
                options.append(name)

        # Add option to search again or create custom
        options.append("🔍 Другой вариант")

        # If we have OCR nutrition data from label, offer to use it
        if food_item.get("ocr_nutrition_fallback"):
            options.append("📋 Использовать данные с этикетки")

        options.append("➕ Создать свой продукт")

        # Show message about total results if more than 5
        total_message = f"Нашел {len(candidates)} вариантов для '{food_name}'"
        if len(candidates) > 5:
            total_message += f" (показываю первые 5)"
        total_message += ":\n\nВыберите подходящий:"

        return {
            "food_candidates": candidates,
            "food_selection_page": 0,  # Reset page for new search
            "clarification_requests": [{
                "type": "food_selection",
                "question": total_message,
                "options": options,
                "context": {
                    "food_name": food_name,
                    "candidate_ids": [c.get("food_id") for c in top_candidates],
                    "total_found": len(candidates)
                }
            }],
            "needs_clarification": True,
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Error searching FatSecret: {e}")
        return {
            "errors": state.get("errors", []) + [f"FatSecret search error: {str(e)}"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }
