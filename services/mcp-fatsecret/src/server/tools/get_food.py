"""
MCP Tool: get_food
Retrieves detailed food information by ID.
"""

from typing import Dict, Any
import json
import logging

from ...client.fatsecret_client import FatSecretClient

logger = logging.getLogger(__name__)


async def get_food_tool(
    food_id: str,
    client: FatSecretClient = None
) -> str:
    """
    Get detailed food information from FatSecret.
    
    Args:
        food_id: FatSecret food ID
        client: FatSecret API client instance
        
    Returns:
        JSON string with food details
    """
    if not client:
        client = FatSecretClient()
    
    try:
        food_data = await client.get_food(food_id)
        
        if not food_data:
            return json.dumps({
                "success": False,
                "error": "Food not found",
                "food_id": food_id
            })
        
        result = {
            "success": True,
            "food_id": food_id,
            "food": food_data
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in get_food_tool: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "food_id": food_id
        })


# Tool metadata for MCP
TOOL_METADATA = {
    "name": "get_food",
    "description": "Get detailed information about a specific food item by its FatSecret ID",
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
