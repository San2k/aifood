"""
LLM Service Router - routes requests to OpenAI or Ollama based on configuration.
Provides a unified interface for text and vision AI operations.
"""

import logging
from typing import Dict, Any, List, Optional

from ..config import settings
from .openai_service import openai_service
from .ollama_service import ollama_service

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service that routes to OpenAI or Ollama based on configuration.
    Falls back to OpenAI if Ollama fails.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        logger.info(f"LLM Service initialized with provider: {self.provider}")

    async def parse_food_text(self, user_input: str) -> Dict[str, Any]:
        """
        Parse food text input using configured LLM provider.
        Falls back to OpenAI if Ollama fails.

        Args:
            user_input: User's text input

        Returns:
            Dict with parsed foods and clarification info
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for text parsing")
                result = await ollama_service.parse_food_text(user_input)

                # Check if Ollama succeeded
                if "error" not in result and result.get("items"):
                    return result

                # Fallback to OpenAI if Ollama failed
                logger.warning("Ollama failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.parse_food_text(user_input)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.parse_food_text(user_input)
                else:
                    return {
                        "items": [],
                        "needs_clarification": True,
                        "clarification_reasons": [f"LLM error: {str(e)}"],
                        "error": str(e)
                    }
        else:
            logger.info("Using OpenAI for text parsing")
            return await openai_service.parse_food_text(user_input)

    async def recognize_food_from_photo(
        self,
        image_url: str,
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize food from photo using configured vision model.
        Falls back to OpenAI if Ollama fails.

        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data

        Returns:
            Dict with product name and search query
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for food recognition")
                result = await ollama_service.recognize_food_from_photo(image_url, image_data)

                # Check if Ollama succeeded
                if "error" not in result and result.get("product_name"):
                    return result

                # Fallback to OpenAI
                logger.warning("Ollama vision failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.recognize_food_from_photo(image_url, image_data)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama vision error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.recognize_food_from_photo(image_url, image_data)
                else:
                    return {
                        "product_name": None,
                        "search_query": None,
                        "error": str(e),
                        "confidence": 0.0
                    }
        else:
            logger.info("Using OpenAI for food recognition")
            return await openai_service.recognize_food_from_photo(image_url, image_data)

    async def parse_nutrition_label(
        self,
        image_url: str,
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse nutrition label from image using configured vision model.

        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data

        Returns:
            Dict with extracted nutrition data
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for nutrition label parsing")
                result = await ollama_service.parse_nutrition_label(image_url, image_data)

                if "error" not in result and result.get("product_name"):
                    return result

                # Fallback
                logger.warning("Ollama vision failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.parse_nutrition_label(image_url, image_data)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama vision error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.parse_nutrition_label(image_url, image_data)
                else:
                    return {
                        "product_name": None,
                        "error": str(e),
                        "confidence": 0.0
                    }
        else:
            logger.info("Using OpenAI for nutrition label parsing")
            return await openai_service.parse_nutrition_label(image_url, image_data)

    async def generate_advice(
        self,
        user_context: Dict[str, Any],
        daily_totals: Dict[str, float],
        recent_entries: List[Dict[str, Any]]
    ) -> str:
        """
        Generate personalized nutrition advice using configured LLM.

        Args:
            user_context: User goals and targets
            daily_totals: Today's nutrition totals
            recent_entries: Recent food log entries

        Returns:
            Advice text
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for advice generation")
                result = await ollama_service.generate_advice(user_context, daily_totals, recent_entries)

                if result and "Unable to generate" not in result:
                    return result

                # Fallback
                logger.warning("Ollama failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.generate_advice(user_context, daily_totals, recent_entries)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.generate_advice(user_context, daily_totals, recent_entries)
                else:
                    return "Unable to generate advice at this time."
        else:
            logger.info("Using OpenAI for advice generation")
            return await openai_service.generate_advice(user_context, daily_totals, recent_entries)

    async def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from natural language input.

        Args:
            user_input: Raw user message

        Returns:
            Dict with intent classification and confidence
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for intent detection")
                result = await ollama_service.detect_intent(user_input)

                if "error" not in result and result.get("intent"):
                    return result

                # Fallback to OpenAI
                logger.warning("Ollama intent detection failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.detect_intent(user_input)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama intent detection error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.detect_intent(user_input)
                else:
                    return {
                        "intent": "food_entry",
                        "confidence": 0.5,
                        "reasoning": f"Error: {str(e)}"
                    }
        else:
            logger.info("Using OpenAI for intent detection")
            return await openai_service.detect_intent(user_input)

    async def generate_conversational_response(
        self,
        user_input: str,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a conversational response for questions and chat.

        Args:
            user_input: User's message
            intent: Detected intent (question or chat)
            user_context: Optional user profile and data

        Returns:
            Conversational response text
        """
        if self.provider == "ollama":
            try:
                logger.info(f"Using Ollama for conversational response (intent: {intent})")
                result = await ollama_service.generate_conversational_response(user_input, intent, user_context)

                if result and "Извините, произошла ошибка" not in result:
                    return result

                # Fallback
                logger.warning("Ollama conversational response failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.generate_conversational_response(user_input, intent, user_context)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama conversational response error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.generate_conversational_response(user_input, intent, user_context)
                else:
                    return "Извините, произошла ошибка. Попробуйте еще раз."
        else:
            logger.info(f"Using OpenAI for conversational response (intent: {intent})")
            return await openai_service.generate_conversational_response(user_input, intent, user_context)

    async def analyze_report_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user's report request to understand what time period they want.

        Args:
            user_input: User's request

        Returns:
            Dict with period type and days count
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama to analyze report request")
                result = await ollama_service.analyze_report_request(user_input)

                if "error" not in result and result.get("period"):
                    return result

                # Fallback to OpenAI
                logger.warning("Ollama analysis failed, falling back to OpenAI")
                if settings.OPENAI_API_KEY:
                    return await openai_service.analyze_report_request(user_input)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama report analysis error, falling back to OpenAI: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.analyze_report_request(user_input)
                else:
                    return {"period": "today", "days": 1, "reasoning": f"Error: {str(e)}"}
        else:
            logger.info("Using OpenAI to analyze report request")
            return await openai_service.analyze_report_request(user_input)

    async def translate_to_english(self, text: str) -> str:
        """
        Translate food name to English for FatSecret search.
        Uses Ollama with OpenAI fallback.

        Args:
            text: Food name in any language (Russian, Ukrainian, etc.)

        Returns:
            English translation of the food name
        """
        if self.provider == "ollama":
            try:
                logger.info("Using Ollama for translation")
                result = await ollama_service.translate_to_english(text)

                # If translation looks valid, return it
                if result and result != text:
                    return result

                # Fallback to OpenAI if translation didn't change (might be unclear)
                if settings.OPENAI_API_KEY and result == text:
                    logger.warning("Ollama translation unchanged, trying OpenAI")
                    return await openai_service.translate_to_english(text)
                else:
                    return result

            except Exception as e:
                logger.error(f"Ollama translation error: {e}")
                if settings.OPENAI_API_KEY:
                    return await openai_service.translate_to_english(text)
                else:
                    return text
        else:
            logger.info("Using OpenAI for translation")
            return await openai_service.translate_to_english(text)


# Global service instance
llm_service = LLMService()
