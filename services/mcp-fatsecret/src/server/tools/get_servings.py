"""
MCP Tool: get_servings
Retrieves all serving options for a food item.
"""

from typing import Dict, Any
import json
import logging

from ...client.fatsecret_client import FatSecretClient

logger = logging.getLogger(__name__)


async def get_servings_tool(
    food_id: str,
    client: FatSecretClient = None
) -> str:
    """
    Get all serving options for a food item.
    
    Args:
        food_id: FatSecret food ID
        client: FatSecret API client instance
        
    Returns:
        JSON string with serving options and nutrition data
    """
    if not client:
        client = FatSecretClient()
    
    try:
        servings = await client.get_servings(food_id)
        
        if not servings:
            return json.dumps({
                "success": False,
                "error": "No servings found",
                "food_id": food_id
            })
        
        result = {
            "success": True,
            "food_id": food_id,
            "total_servings": len(servings),
            "servings": [
                {
                    "serving_id": s.serving_id,
                    "serving_description": s.serving_description,
                    "metric_serving_amount": s.metric_serving_amount,
                    "metric_serving_unit": s.metric_serving_unit,
                    "number_of_units": s.number_of_units,
                    "measurement_description": s.measurement_description,
                    "nutrition": {
                        "calories": s.calories,
                        "carbohydrate": s.carbohydrate,
                        "protein": s.protein,
                        "fat": s.fat,
                        "saturated_fat": s.saturated_fat,
                        "polyunsaturated_fat": s.polyunsaturated_fat,
                        "monounsaturated_fat": s.monounsaturated_fat,
                        "trans_fat": s.trans_fat,
                        "cholesterol": s.cholesterol,
                        "sodium": s.sodium,
                        "potassium": s.potassium,
                        "fiber": s.fiber,
                        "sugar": s.sugar
                    }
                }
                for s in servings
            ]
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in get_servings_tool: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "food_id": food_id
        })


# Tool metadata for MCP
TOOL_METADATA = {
    "name": "get_servings",
    "description": "Get all available serving options with nutrition data for a specific food item",
    "input_schema": {
        "type": "object",
        "properties": {
            "food_id": {
                "type": "string",
                "description": "FatSecret food ID (obtained from search_food)"
            }
        },
        "required": ["food_id"]
    }
}
