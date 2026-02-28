"""
LangGraph Node: show_more_foods
Shows paginated food search results.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..state import NutritionBotState

logger = logging.getLogger(__name__)


async def show_more_foods(state: NutritionBotState) -> Dict[str, Any]:
    """
    Show next page of food search results.

    Args:
        state: Current graph state

    Returns:
        State updates with paginated results
    """
    food_candidates = state.get("food_candidates", [])
    parsed_foods = state.get("parsed_foods", [])
    current_page = state.get("food_selection_page", 0)

    if not food_candidates:
        logger.warning("No food candidates available for pagination")
        return {
            "errors": state.get("errors", []) + ["No results to paginate"],
            "should_end": True,
            "updated_at": datetime.utcnow()
        }

    # Calculate pagination
    page_size = 5
    start_idx = current_page * page_size
    end_idx = start_idx + page_size

    # Get current page candidates
    page_candidates = food_candidates[start_idx:end_idx]

    if not page_candidates:
        # No more results, loop back to first page
        logger.info("No more results, showing first page")
        current_page = 0
        start_idx = 0
        end_idx = page_size
        page_candidates = food_candidates[start_idx:end_idx]

    # Get food name from context
    food_name = parsed_foods[0].get("name", "продукт") if parsed_foods else "продукт"

    # Format options for display
    options = []
    for c in page_candidates:
        brand = c.get('brand_name', 'Generic')
        name = c.get('food_name', '')
        if brand and brand.lower() != 'generic':
            options.append(f"{name} ({brand})")
        else:
            options.append(name)

    # Add navigation buttons
    has_more = end_idx < len(food_candidates)
    has_previous = current_page > 0

    if has_previous:
        options.append("◀️ Предыдущие")

    if has_more:
        options.append("🔍 Другой вариант")

    options.append("➕ Создать свой продукт")

    # Create question text
    total_results = len(food_candidates)
    showing_range = f"{start_idx + 1}-{min(end_idx, total_results)}"
    question = f"Показываю варианты {showing_range} из {total_results} для '{food_name}':\n\nВыберите подходящий:"

    logger.info(f"Showing page {current_page + 1} of food results ({showing_range}/{total_results})")

    return {
        "clarification_requests": [{
            "type": "food_selection",
            "question": question,
            "options": options,
            "context": {
                "food_name": food_name,
                "page": current_page,
                "total_found": total_results
            }
        }],
        "needs_clarification": True,
        "should_end": True,
        "updated_at": datetime.utcnow()
    }
