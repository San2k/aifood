"""
FatSecret Platform API Client.
Handles OAuth2 authentication and API requests to FatSecret.
"""

import httpx
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class Food:
    """Food data from FatSecret API."""
    food_id: str
    food_name: str
    food_type: str
    brand_name: Optional[str] = None
    food_description: Optional[str] = None


@dataclass
class Serving:
    """Serving data from FatSecret API."""
    serving_id: str
    serving_description: str
    serving_url: Optional[str] = None
    metric_serving_amount: Optional[float] = None
    metric_serving_unit: Optional[str] = None
    number_of_units: Optional[float] = None
    measurement_description: Optional[str] = None
    calories: Optional[float] = None
    carbohydrate: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    saturated_fat: Optional[float] = None
    polyunsaturated_fat: Optional[float] = None
    monounsaturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None


class FatSecretClient:
    """Client for interacting with FatSecret Platform API."""

    def __init__(self):
        self.client_id = settings.FATSECRET_CLIENT_ID
        self.client_secret = settings.FATSECRET_CLIENT_SECRET
        self.api_url = settings.FATSECRET_API_URL
        self.token_url = settings.FATSECRET_TOKEN_URL
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token using client credentials flow."""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if time.time() < self.token_expires_at:
                return self.access_token

        # Request new token
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "scope": "basic"
                    },
                    auth=(self.client_id, self.client_secret),
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                self.access_token = data["access_token"]
                # Set expiration with 5 minute buffer
                self.token_expires_at = time.time() + data["expires_in"] - 300
                
                logger.info("FatSecret access token obtained successfully")
                return self.access_token
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to get FatSecret access token: {e}")
                raise

    async def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to FatSecret API."""
        token = await self._get_access_token()
        
        # Add method to params
        params["method"] = method
        params["format"] = "json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {token}"},
                    data=params,
                    timeout=15.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"FatSecret API request failed: {e}")
                raise

    async def search_foods(
        self, 
        query: str, 
        max_results: int = 10,
        page_number: int = 0
    ) -> List[Food]:
        """
        Search for foods in FatSecret database.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default: 10)
            page_number: Page number for pagination (default: 0)
            
        Returns:
            List of Food objects
        """
        try:
            response = await self._make_request(
                "foods.search",
                {
                    "search_expression": query,
                    "max_results": str(max_results),
                    "page_number": str(page_number)
                }
            )
            
            # Parse response
            foods_data = response.get("foods", {})
            food_list = foods_data.get("food", [])
            
            # Handle single food result (API returns dict instead of list)
            if isinstance(food_list, dict):
                food_list = [food_list]
            
            foods = []
            for food_data in food_list:
                foods.append(Food(
                    food_id=food_data.get("food_id"),
                    food_name=food_data.get("food_name"),
                    food_type=food_data.get("food_type"),
                    brand_name=food_data.get("brand_name"),
                    food_description=food_data.get("food_description")
                ))
            
            logger.info(f"Found {len(foods)} foods for query: {query}")
            return foods
            
        except Exception as e:
            logger.error(f"Error searching foods: {e}")
            return []

    async def get_food(self, food_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed food information by ID.
        
        Args:
            food_id: FatSecret food ID
            
        Returns:
            Food details dictionary
        """
        try:
            response = await self._make_request(
                "food.get.v3",
                {"food_id": food_id}
            )
            
            food_data = response.get("food", {})
            logger.info(f"Retrieved food details for ID: {food_id}")
            return food_data
            
        except Exception as e:
            logger.error(f"Error getting food {food_id}: {e}")
            return None

    async def get_servings(self, food_id: str) -> List[Serving]:
        """
        Get all serving options for a food.
        
        Args:
            food_id: FatSecret food ID
            
        Returns:
            List of Serving objects
        """
        try:
            food_data = await self.get_food(food_id)
            if not food_data:
                return []
            
            servings_data = food_data.get("servings", {}).get("serving", [])
            
            # Handle single serving result
            if isinstance(servings_data, dict):
                servings_data = [servings_data]
            
            servings = []
            for serving_data in servings_data:
                servings.append(Serving(
                    serving_id=serving_data.get("serving_id"),
                    serving_description=serving_data.get("serving_description"),
                    serving_url=serving_data.get("serving_url"),
                    metric_serving_amount=self._to_float(serving_data.get("metric_serving_amount")),
                    metric_serving_unit=serving_data.get("metric_serving_unit"),
                    number_of_units=self._to_float(serving_data.get("number_of_units")),
                    measurement_description=serving_data.get("measurement_description"),
                    calories=self._to_float(serving_data.get("calories")),
                    carbohydrate=self._to_float(serving_data.get("carbohydrate")),
                    protein=self._to_float(serving_data.get("protein")),
                    fat=self._to_float(serving_data.get("fat")),
                    saturated_fat=self._to_float(serving_data.get("saturated_fat")),
                    polyunsaturated_fat=self._to_float(serving_data.get("polyunsaturated_fat")),
                    monounsaturated_fat=self._to_float(serving_data.get("monounsaturated_fat")),
                    trans_fat=self._to_float(serving_data.get("trans_fat")),
                    cholesterol=self._to_float(serving_data.get("cholesterol")),
                    sodium=self._to_float(serving_data.get("sodium")),
                    potassium=self._to_float(serving_data.get("potassium")),
                    fiber=self._to_float(serving_data.get("fiber")),
                    sugar=self._to_float(serving_data.get("sugar"))
                ))
            
            logger.info(f"Retrieved {len(servings)} servings for food {food_id}")
            return servings
            
        except Exception as e:
            logger.error(f"Error getting servings for food {food_id}: {e}")
            return []

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """Convert value to float, return None if conversion fails."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
