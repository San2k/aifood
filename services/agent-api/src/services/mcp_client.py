"""
FatSecret API Client.
Direct integration with FatSecret API for food search and nutrition data.
"""

import logging
import httpx
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..config import settings

logger = logging.getLogger(__name__)


class MCPFatSecretClient:
    """Client for FatSecret API service."""

    BASE_URL = "https://platform.fatsecret.com/rest/server.api"
    TOKEN_URL = "https://oauth.fatsecret.com/connect/token"

    def __init__(self):
        self.client_id = settings.FATSECRET_CLIENT_ID
        self.client_secret = settings.FATSECRET_CLIENT_SECRET
        self.access_token = None
        self.token_expires_at = None
        logger.info("FatSecret API client initialized")

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth 2.0 access token."""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        # Get new token using client credentials flow
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "basic"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    headers=headers,
                    data=data,
                    timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()

                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

                logger.info("Successfully obtained FatSecret access token")
                return self.access_token

        except httpx.HTTPError as e:
            logger.error(f"Failed to get FatSecret access token: {e}")
            raise

    async def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to FatSecret API."""
        token = await self._get_access_token()

        params["method"] = method
        params["format"] = "json"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    data=params,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                logger.debug(f"FatSecret API response: {result}")
                return result
        except httpx.HTTPError as e:
            logger.error(f"FatSecret API error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response body: {e.response.text}")
            raise

    async def search_foods(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for foods in FatSecret database.

        Args:
            query: Food search query
            max_results: Maximum number of results

        Returns:
            List of food items
        """
        try:
            result = await self._make_request(
                "foods.search",
                {
                    "search_expression": query,
                    "max_results": max_results,
                    "page_number": 0
                }
            )

            # DEBUG: Log full response to understand structure
            logger.info(f"Full FatSecret API response for query '{query}': {result}")

            # Parse FatSecret response
            foods_result = result.get("foods", {})
            logger.info(f"foods_result extracted: {foods_result}")

            # Check if we have actual food results
            # FatSecret returns total_results as string "0" when no results
            total_results = foods_result.get("total_results", "0")
            if total_results == "0" or not foods_result.get("food"):
                logger.warning(f"No food results for query '{query}' (total_results={total_results})")
                return []

            food_list = foods_result.get("food", [])
            # Handle single result (not in a list)
            if isinstance(food_list, dict):
                food_list = [food_list]

            foods = []
            for food in food_list:
                foods.append({
                    "food_id": food.get("food_id"),
                    "food_name": food.get("food_name"),
                    "brand_name": food.get("brand_name"),
                    "food_type": food.get("food_type"),
                    "food_url": food.get("food_url")
                })

            logger.info(f"Found {len(foods)} foods for query: {query}")
            return foods

        except Exception as e:
            logger.error(f"Error searching foods: {e}")
            return []

    async def get_food(self, food_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed food information.

        Args:
            food_id: FatSecret food ID

        Returns:
            Food details dictionary
        """
        try:
            result = await self._make_request(
                "food.get.v2",
                {"food_id": food_id}
            )

            food = result.get("food")
            if not food:
                return None

            logger.info(f"Retrieved food: {food_id}")
            return food

        except Exception as e:
            logger.error(f"Error getting food: {e}")
            return None

    async def get_servings(self, food_id: str) -> List[Dict[str, Any]]:
        """
        Get serving options for a food.

        Args:
            food_id: FatSecret food ID

        Returns:
            List of serving options with nutrition data
        """
        try:
            food = await self.get_food(food_id)
            if not food:
                return []

            servings_data = food.get("servings", {})
            serving_list = servings_data.get("serving", [])

            # Handle single serving (not in a list)
            if isinstance(serving_list, dict):
                serving_list = [serving_list]

            servings = []
            for serving in serving_list:
                # Convert metric_serving_amount to float (API returns string)
                metric_amount = serving.get("metric_serving_amount")
                metric_amount_float = float(metric_amount) if metric_amount else None

                # Convert number_of_units to float if present
                num_units = serving.get("number_of_units")
                num_units_float = float(num_units) if num_units else None

                servings.append({
                    "serving_id": serving.get("serving_id"),
                    "serving_description": serving.get("serving_description"),
                    "serving_url": serving.get("serving_url"),
                    "metric_serving_amount": metric_amount_float,
                    "metric_serving_unit": serving.get("metric_serving_unit"),
                    "number_of_units": num_units_float,
                    "measurement_description": serving.get("measurement_description"),
                    "calories": float(serving.get("calories", 0)),
                    "carbohydrate": float(serving.get("carbohydrate", 0)),
                    "protein": float(serving.get("protein", 0)),
                    "fat": float(serving.get("fat", 0)),
                    "saturated_fat": float(serving.get("saturated_fat", 0)),
                    "polyunsaturated_fat": float(serving.get("polyunsaturated_fat", 0)),
                    "monounsaturated_fat": float(serving.get("monounsaturated_fat", 0)),
                    "cholesterol": float(serving.get("cholesterol", 0)),
                    "sodium": float(serving.get("sodium", 0)),
                    "potassium": float(serving.get("potassium", 0)),
                    "fiber": float(serving.get("fiber", 0)),
                    "sugar": float(serving.get("sugar", 0))
                })

            logger.info(f"Retrieved {len(servings)} servings for food: {food_id}")
            return servings

        except Exception as e:
            logger.error(f"Error getting servings: {e}")
            return []


# Global client instance
mcp_client = MCPFatSecretClient()
