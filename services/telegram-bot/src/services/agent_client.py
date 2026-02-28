"""
Agent API client for communicating with the agent service.
"""

import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class AgentClient:
    """Client for interacting with the Agent API."""

    def __init__(self, base_url: str):
        """
        Initialize the agent client.

        Args:
            base_url: Base URL of the agent API
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def ingest_message(
        self,
        telegram_id: int,
        message: str,
        message_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        input_type: Literal["text", "photo", "callback", "confirmation"] = "text",
        photo_file_id: Optional[str] = None,
        clarification_responses: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the agent for processing.

        Args:
            telegram_id: Telegram user ID
            message: User message text
            message_id: Telegram message ID
            username: Telegram username (optional)
            first_name: User first name (optional)
            last_name: User last name (optional)
            conversation_id: Conversation ID for multi-turn (optional)
            input_type: Input type (text/photo/callback/confirmation)
            photo_file_id: Photo file ID (if photo message)
            clarification_responses: User responses to clarifications (optional)
            timestamp: Message timestamp (optional)

        Returns:
            Agent response dict with status and messages
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "telegram_id": telegram_id,
                    "message": message,
                    "message_id": message_id,
                    "input_type": input_type
                }

                # Add optional fields if provided
                if username is not None:
                    payload["username"] = username
                if first_name is not None:
                    payload["first_name"] = first_name
                if last_name is not None:
                    payload["last_name"] = last_name
                if conversation_id is not None:
                    payload["conversation_id"] = conversation_id
                if photo_file_id is not None:
                    payload["photo_file_id"] = photo_file_id
                if clarification_responses is not None:
                    payload["clarification_responses"] = clarification_responses
                if timestamp is not None:
                    payload["timestamp"] = timestamp.isoformat()

                response = await client.post(
                    f"{self.base_url}/v1/ingest",
                    json=payload
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout calling agent API")
            return {
                "success": False,
                "reply_text": "Извините, запрос занял слишком много времени. Попробуйте еще раз.",
                "errors": ["timeout"]
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from agent API: {e.response.status_code}")
            return {
                "success": False,
                "reply_text": "Извините, произошла ошибка при обработке запроса.",
                "errors": [f"http_{e.response.status_code}"]
            }
        except Exception as e:
            logger.error(f"Error calling agent API: {e}", exc_info=True)
            return {
                "success": False,
                "reply_text": "Извините, произошла ошибка. Попробуйте еще раз.",
                "errors": [str(e)]
            }

    async def get_user_profile(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile from agent API.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User profile dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/users/{telegram_id}/profile"
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error getting user profile: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}", exc_info=True)
            return None

    async def update_user_goals(
        self,
        telegram_id: int,
        daily_calories: Optional[float] = None,
        daily_protein: Optional[float] = None,
        daily_carbs: Optional[float] = None,
        daily_fat: Optional[float] = None
    ) -> bool:
        """
        Update user daily goals.

        Args:
            telegram_id: Telegram user ID
            daily_calories: Daily calorie goal
            daily_protein: Daily protein goal (g)
            daily_carbs: Daily carbs goal (g)
            daily_fat: Daily fat goal (g)

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "daily_calories": daily_calories,
                    "daily_protein": daily_protein,
                    "daily_carbs": daily_carbs,
                    "daily_fat": daily_fat
                }

                response = await client.put(
                    f"{self.base_url}/v1/users/{telegram_id}/goals",
                    json=payload
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Error updating user goals: {e}", exc_info=True)
            return False
