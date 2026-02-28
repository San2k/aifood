"""
MCP Tool: search_food
Searches for foods in FatSecret database.
"""

from typing import Dict, Any
import json
import logging

from ...client.fatsecret_client import FatSecretClient

logger = logging.getLogger(__name__)


async def search_food_tool(
    query: str,
    max_results: int = 10,
    page: int = 0,
    client: FatSecretClient = None
) -> str:
    """
    Search for foods in FatSecret database.
    
    Args:
        query: Food name to search for
        max_results: Maximum number of results (default: 10)
        page: Page number for pagination (default: 0)
        client: FatSecret API client instance
        
    Returns:
        JSON string with search results
    """
    if not client:
        client = FatSecretClient()
    
    try:
        foods = await client.search_foods(query, max_results, page)
        
        result = {
            "success": True,
            "query": query,
            "total_results": len(foods),
            "page": page,
            "foods": [
                {
                    "food_id": food.food_id,
                    "food_name": food.food_name,
                    "food_type": food.food_type,
                    "brand_name": food.brand_name,
                    "food_description": food.food_description
                }
                for food in foods
            ]
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in search_food_tool: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query
        })


# Tool metadata for MCP
TOOL_METADATA = {
    "name": "search_food",
    "description": "Search for foods in the FatSecret database by name or description",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Food name or search query (e.g., 'eggs', 'chicken breast', 'apple')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10
            },
            "page": {
                "type": "integer",
                "description": "Page number for pagination (starts from 0)",
                "default": 0
            }
        },
        "required": ["query"]
    }
}
