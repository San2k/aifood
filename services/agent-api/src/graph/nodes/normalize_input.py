"""
LangGraph Node: normalize_input
Parses text input using GPT-4 to extract food items.
"""

import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from ..state import NutritionBotState
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)


def fallback_parse(text: str) -> List[Dict[str, Any]]:
    """
    Simple fallback parser when OpenAI is unavailable.
    Extracts basic food information using regex patterns.
    """
    # Pattern: optional number, optional unit, food name
    # Examples: "150г гречка", "2 яйца", "яблоко", "apple 100g"

    # Remove common prefixes
    text = re.sub(r'^(съел|ел|ate|had)\s+', '', text, flags=re.IGNORECASE)

    # Split by common separators
    items = re.split(r'[,;и]', text)

    parsed_foods = []

    for item in items:
        item = item.strip()
        if not item:
            continue

        # Try to extract quantity and unit
        # Pattern: number + optional unit (г, г., грамм, g)
        quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*(г\.?|грамм|gramm?|ml|мл)?', item, re.IGNORECASE)

        quantity = None
        unit = "g"
        food_name = item

        if quantity_match:
            quantity = float(quantity_match.group(1))
            unit_str = quantity_match.group(2)
            if unit_str:
                unit = unit_str.lower().replace('.', '').replace('рамм', '')[:2]
            # Remove quantity from food name
            food_name = item[:quantity_match.start()] + item[quantity_match.end():]

        food_name = food_name.strip()

        if food_name:
            parsed_foods.append({
                "name": food_name,
                "quantity": quantity,
                "unit": unit if quantity else None,
                "cooking_method": None,
                "notes": None
            })

    return parsed_foods


async def normalize_input(state: NutritionBotState) -> Dict[str, Any]:
    """
    Parse user text input to extract food items, quantities, and units.
    
    Uses OpenAI GPT-4 to parse natural language food descriptions.
    Detects if clarification is needed (missing weights, cooking methods, etc.).
    
    Args:
        state: Current graph state
        
    Returns:
        State updates with parsed foods and clarification status
    """
    raw_input = state.get("raw_input", "")
    
    logger.info(f"Normalizing text input: {raw_input[:50]}...")
    
    try:
        # Try to parse food text with LLM (Ollama or OpenAI)
        parse_result = await llm_service.parse_food_text(raw_input)

        # Check if OpenAI failed (returns error key)
        if "error" in parse_result or not parse_result.get("items"):
            # Fallback to simple regex parser if OpenAI fails
            logger.warning(f"OpenAI parse failed or returned 0 items, using fallback parser")
            parsed_foods = fallback_parse(raw_input)
            needs_clarification = any(not f.get("quantity") for f in parsed_foods)
            clarification_reasons = ["Using fallback parser"]
            logger.info(f"Parsed {len(parsed_foods)} food items with fallback parser")
        else:
            parsed_foods = parse_result.get("items", [])
            needs_clarification = parse_result.get("needs_clarification", False)
            clarification_reasons = parse_result.get("clarification_reasons", [])
            logger.info(f"Parsed {len(parsed_foods)} food items with OpenAI")

        logger.info(f"Total parsed: {len(parsed_foods)} food items, needs_clarification={needs_clarification}")

        # Check if any items have custom nutrition data
        custom_entries = []
        for food_item in parsed_foods:
            if food_item.get("custom_nutrition"):
                custom_entries.append(food_item)

        if custom_entries:
            logger.info(f"Found {len(custom_entries)} items with custom nutrition data")

        updates = {
            "parsed_foods": parsed_foods,
            "has_custom_nutrition": len(custom_entries) > 0,
            "updated_at": datetime.utcnow()
        }

        # Generate clarification requests if needed
        if needs_clarification and clarification_reasons:
            clarification_requests = []
            
            for i, food_item in enumerate(parsed_foods):
                food_name = food_item.get("name", "")
                missing_info = []
                
                # Check what's missing
                if not food_item.get("quantity"):
                    missing_info.append("quantity")
                
                if food_name and not food_item.get("cooking_method"):
                    # Common foods that need cooking method clarification
                    needs_cooking = any(
                        word in food_name.lower() 
                        for word in ["гречка", "рис", "rice", "buckwheat", "pasta", "макароны", "курица", "chicken", "мясо", "meat"]
                    )
                    if needs_cooking:
                        missing_info.append("cooking_method")
                
                if missing_info:
                    question = f"Для '{food_name}': "
                    
                    if "quantity" in missing_info:
                        question += "Сколько грамм? "
                    
                    if "cooking_method" in missing_info:
                        question += "Сырое или приготовленное (варёное/жареное)?"
                    
                    clarification_requests.append({
                        "type": "weight" if "quantity" in missing_info else "cooking_method",
                        "question": question.strip(),
                        "options": None,
                        "context": {
                            "food_index": i,
                            "food_name": food_name,
                            "missing_info": missing_info
                        }
                    })
            
            updates["clarification_requests"] = clarification_requests
            updates["needs_clarification"] = True
            updates["next_node"] = "need_clarification"
        else:
            # Check if we have custom nutrition entries
            if updates.get("has_custom_nutrition"):
                # Route to custom nutrition processing
                updates["needs_clarification"] = False
                updates["next_node"] = "process_custom_nutrition"
                logger.info("Routing to process_custom_nutrition node")
            else:
                # No clarification needed, proceed to FatSecret search
                updates["needs_clarification"] = False
                updates["next_node"] = "fatsecret_search"
                logger.info("Routing to fatsecret_search node")

        return updates
        
    except Exception as e:
        logger.error(f"Error normalizing input: {e}")
        return {
            "errors": state.get("errors", []) + [f"Parse error: {str(e)}"],
            "updated_at": datetime.utcnow(),
            "should_end": True
        }
