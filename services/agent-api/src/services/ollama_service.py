"""
Ollama Service for text parsing and Vision OCR using local models.
Handles all interactions with Ollama API.
"""

import logging
from typing import Dict, Any, List, Optional
import json
import base64
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for Ollama API interactions."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_text = settings.OLLAMA_MODEL_TEXT
        self.model_vision = settings.OLLAMA_MODEL_VISION
        self.timeout = settings.OLLAMA_TIMEOUT

    async def parse_food_text(self, user_input: str) -> Dict[str, Any]:
        """
        Parse food text input using Ollama (Mistral).
        Extracts food items, quantities, and determines if clarification needed.

        Args:
            user_input: User's text input (e.g., "2 eggs and 150g buckwheat")

        Returns:
            Dict with parsed foods and clarification info
        """
        system_prompt = """You are a food input parser. Extract food items from user text.
DO NOT calculate nutrition values UNLESS user provides them directly.
Return ONLY valid JSON.

OUTPUT SCHEMA:
{
  "items": [
    {
      "name": "food name in original language",
      "quantity": number or null,
      "unit": "g" | "ml" | "шт" | "oz" | "cup" | null,
      "cooking_method": "raw" | "cooked" | "fried" | "boiled" | null,
      "notes": "any additional info",
      "custom_nutrition": {
        "calories": number or null,
        "protein": number or null,
        "carbs": number or null,
        "fat": number or null,
        "is_per_100g": boolean
      } or null
    }
  ],
  "needs_clarification": boolean,
  "clarification_reasons": ["reason1", "reason2"]
}

RULES FOR REGULAR FOOD:
- If weight/quantity missing → needs_clarification = true
- If cooking method ambiguous (e.g., "гречка" without "сырая"/"варёная") → needs_clarification = true
- Preserve original language for food names
- Do NOT translate food names
- Extract all mentioned foods

RULES FOR CUSTOM NUTRITION INPUT:
User can provide nutrition data directly in formats like:
- "БЖУ 50/50/50 калорий 150" → {protein: 50, fat: 50, carbs: 50, calories: 150, is_per_100g: false}
- "КБЖУ 150/50/50/50" → {calories: 150, protein: 50, fat: 50, carbs: 50, is_per_100g: false}
- "калорий 250 БЖУ 30/20/10 на 100г" → {calories: 250, protein: 30, fat: 20, carbs: 10, is_per_100g: true}
- "на 100 грамм: калории 350, белки 20, жиры 10, углеводы 40" → {calories: 350, protein: 20, fat: 10, carbs: 40, is_per_100g: true}

When user provides nutrition data:
1. Extract exact values (do NOT calculate anything)
2. Set is_per_100g = true if user says "на 100г" / "per 100g" / "на 100 грамм"
3. Set is_per_100g = false otherwise (values are for total portion)
4. If nutrition provided but weight missing → needs_clarification = true, ask for weight
5. Include all nutrition data in custom_nutrition field

Example:
Input: "Съел скрэмбл с овощным миксом КБЖУ 280/14/23/6"
Output: {
  "items": [{
    "name": "скрэмбл с овощным миксом",
    "quantity": null,
    "unit": "g",
    "custom_nutrition": {
      "calories": 280,
      "protein": 14,
      "fat": 23,
      "carbs": 6,
      "is_per_100g": false
    }
  }],
  "needs_clarification": true,
  "clarification_reasons": ["Weight not specified for custom nutrition"]
}"""

        prompt = f"{system_prompt}\n\nUSER INPUT: {user_input}\n\nReturn only valid JSON:"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1000
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                # Parse the response
                response_text = result_data.get("response", "{}")
                result = json.loads(response_text)

                logger.info(f"Parsed food text: {len(result.get('items', []))} items found")
                return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            return {
                "items": [],
                "needs_clarification": True,
                "clarification_reasons": [f"Parsing error: {str(e)}"],
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error parsing food text with Ollama: {e}")
            return {
                "items": [],
                "needs_clarification": True,
                "clarification_reasons": [f"Parsing error: {str(e)}"],
                "error": str(e)
            }

    async def recognize_food_from_photo(
        self,
        image_url: str,
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize food product from package photo using Ollama Vision (LLaVA).
        Extracts product name, brand, and basic info for searching.

        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data (alternative to URL)

        Returns:
            Dict with product name and search query
        """
        prompt = """Look at this food product package and identify what it is.

Return a JSON object with this exact structure:
{
  "product_name": "specific product name in original language",
  "brand": "brand name or null",
  "food_type": "general food category",
  "search_query": "optimized search term for food database",
  "confidence": 0.8,
  "notes": "any additional details"
}

RULES:
- Extract the exact product name visible on package
- Identify the brand if visible
- Create a search_query that's generic enough to find in food databases
- Confidence based on image clarity and text visibility"""

        try:
            # Prepare image - Ollama expects base64
            if image_data:
                image_b64 = image_data
            else:
                # Download image from URL
                async with httpx.AsyncClient() as client:
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()
                    image_b64 = base64.b64encode(img_response.content).decode('utf-8')

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_vision,
                        "prompt": prompt,
                        "images": [image_b64],
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 500
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                # Parse the response
                response_text = result_data.get("response", "{}")
                result = json.loads(response_text)

                logger.info(f"Recognized food from photo: {result.get('product_name', 'Unknown')}")
                return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama vision response: {e}")
            return {
                "product_name": None,
                "search_query": None,
                "error": str(e),
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Error recognizing food from photo with Ollama: {e}")
            return {
                "product_name": None,
                "search_query": None,
                "error": str(e),
                "confidence": 0.0
            }

    async def parse_nutrition_label(
        self,
        image_url: str,
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse nutrition label from image using Ollama Vision (LLaVA).

        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data (alternative to URL)

        Returns:
            Dict with extracted nutrition data
        """
        prompt = """You are reading a food nutrition label. Extract the EXACT numbers you see.

STEP 1: Find the product name at the top of the label.
STEP 2: Find the nutrition facts table. Look for these rows:
  - Calories / Калории / Энергетическая ценность
  - Protein / Белки / Белок
  - Carbohydrates / Углеводы / Carbs
  - Fat / Жиры / Жир

STEP 3: Read the EXACT number next to each nutrient. Do not invent or guess.
STEP 4: Find the weight indicator (e.g., "на 100г", "per 160g", "на порцию 160г")

Return JSON:
{
  "product_name": "exact text from label",
  "brand": "brand name if visible, else null",
  "serving_size": {"value": number_or_null, "unit": "g or ml or null"},
  "servings_per_container": number_or_null,
  "nutrition_values": {
    "calories": EXACT_number_from_calories_row,
    "protein": EXACT_number_from_protein_row,
    "carbs": EXACT_number_from_carbs_row,
    "fat": EXACT_number_from_fat_row,
    "fiber": EXACT_number_from_fiber_row_or_null,
    "sugar": EXACT_number_from_sugar_row_or_null,
    "sodium": EXACT_number_from_sodium_row_or_null
  },
  "nutrition_per_serving_weight": weight_in_grams_for_above_values,
  "ingredients": "ingredients text or null",
  "confidence": 0.0_to_1.0
}

CRITICAL:
- DO NOT calculate or convert anything
- DO NOT use example numbers
- READ the actual printed numbers from the image
- If a number is 0, write 0 (not null)
- If a number is not visible, write null
- "nutrition_per_serving_weight" = the weight for which nutrition values are shown (e.g., 100 if label says "на 100г", 160 if label says "на порцию 160г")"""

        try:
            # Prepare image
            if image_data:
                image_b64 = image_data
            else:
                async with httpx.AsyncClient() as client:
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()
                    image_b64 = base64.b64encode(img_response.content).decode('utf-8')

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_vision,
                        "prompt": prompt,
                        "images": [image_b64],
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 1500
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                response_text = result_data.get("response", "{}")
                result = json.loads(response_text)

                logger.info(f"Parsed nutrition label: {result.get('product_name', 'Unknown')}")
                return result

        except Exception as e:
            logger.error(f"Error parsing nutrition label with Ollama: {e}")
            return {
                "product_name": None,
                "error": str(e),
                "confidence": 0.0
            }

    async def generate_advice(
        self,
        user_context: Dict[str, Any],
        daily_totals: Dict[str, float],
        recent_entries: List[Dict[str, Any]]
    ) -> str:
        """
        Generate personalized nutrition advice using Ollama (Mistral).

        Args:
            user_context: User goals and targets
            daily_totals: Today's nutrition totals
            recent_entries: Recent food log entries

        Returns:
            Advice text
        """
        system_prompt = """You are a nutrition advisor.
Base advice ONLY on logged food data provided.
DO NOT invent nutrition facts.
DO NOT provide medical advice.

INSTRUCTIONS:
1. Compare actual intake vs target goals
2. Suggest practical adjustments (more protein, less sugar, etc.)
3. Recommend specific food swaps if helpful
4. Keep advice actionable and supportive
5. Max 3-4 sentences
6. Use friendly, encouraging tone"""

        user_prompt = f"""User context:
Goal: {user_context.get('goal', 'maintenance')}
Targets: {user_context.get('target_calories', 2000)} kcal, {user_context.get('target_protein', 100)}g protein

Today's totals:
Calories: {daily_totals.get('calories', 0)} kcal
Protein: {daily_totals.get('protein', 0)}g
Carbs: {daily_totals.get('carbs', 0)}g
Fat: {daily_totals.get('fat', 0)}g

Recent foods: {', '.join([e.get('food_name', '') for e in recent_entries[:5]])}

Provide brief, actionable nutrition advice."""

        prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 300
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                advice = result_data.get("response", "").strip()
                logger.info("Generated nutrition advice with Ollama")
                return advice

        except Exception as e:
            logger.error(f"Error generating advice with Ollama: {e}")
            return "Unable to generate advice at this time. Please try again later."

    async def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from natural language input.

        Args:
            user_input: Raw user message

        Returns:
            Dict with intent classification and confidence
        """
        system_prompt = """You are an intent classifier for a nutrition tracking bot.
Classify user messages into one of these intents:

1. "food_entry" - User is logging food they ate
   Examples: "съел 2 яйца", "ate an apple", "100g chicken breast"

2. "view_report" - User wants to see their food log/report
   Examples: "покажи что я съел", "show my log", "what did I eat today"

3. "question" - User is asking a nutrition-related question
   Examples: "сколько калорий мне нужно?", "is protein important?", "what's healthy?"

4. "chat" - Greetings, thanks, small talk
   Examples: "привет", "спасибо", "hello", "thanks"

Return ONLY valid JSON with this structure:
{
  "intent": "food_entry" | "view_report" | "question" | "chat",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}"""

        prompt = f"{system_prompt}\n\nUSER MESSAGE: {user_input}\n\nClassify this message:"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 200
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                response_text = result_data.get("response", "{}")
                result = json.loads(response_text)

                logger.info(f"Detected intent: {result.get('intent')} (confidence: {result.get('confidence')})")
                return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent detection JSON: {e}")
            # Default to food_entry if parsing fails
            return {
                "intent": "food_entry",
                "confidence": 0.5,
                "reasoning": "Fallback - assuming food entry"
            }
        except Exception as e:
            logger.error(f"Error detecting intent with Ollama: {e}")
            return {
                "intent": "food_entry",
                "confidence": 0.5,
                "reasoning": f"Error: {str(e)}"
            }

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
        if intent == "chat":
            system_prompt = """You are a friendly nutrition tracking assistant.
Respond to greetings and small talk warmly and briefly.
Keep responses 1-2 sentences.
Always encourage healthy eating habits."""

            prompt = f"{system_prompt}\n\nUSER: {user_input}\n\nRespond naturally:"

        elif intent == "question":
            system_prompt = """You are a knowledgeable nutrition assistant.
Answer nutrition questions accurately and helpfully.
Base answers on scientific nutrition facts.
Keep responses 2-3 sentences, actionable and clear.
DO NOT provide medical advice - suggest consulting professionals for health issues."""

            context_info = ""
            if user_context:
                goal = user_context.get('goal', 'maintenance')
                target_cals = user_context.get('target_calories', 2000)
                context_info = f"\n\nUser context: Goal={goal}, Target={target_cals} kcal/day"

            prompt = f"{system_prompt}\n\nUSER QUESTION: {user_input}{context_info}\n\nAnswer helpfully:"

        elif intent == "view_report":
            # For view_report, we return a message directing to /today or /week
            return "Для просмотра дневника используйте команды:\n• /today - сегодняшний отчёт\n• /week - недельный отчёт"

        else:
            return "Извините, не понял ваш запрос. Попробуйте переформулировать или используйте /help."

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 250
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                response_text = result_data.get("response", "").strip()
                logger.info(f"Generated conversational response for intent: {intent}")
                return response_text

        except Exception as e:
            logger.error(f"Error generating conversational response with Ollama: {e}")
            return "Извините, произошла ошибка. Попробуйте еще раз."

    async def analyze_report_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user's report request to understand what time period they want.

        Args:
            user_input: User's request (e.g., "show all records", "today", "this week")

        Returns:
            Dict with period type and days count
        """
        system_prompt = """You are analyzing a user's request to view their food log.
Determine what time period they want to see.

Return JSON with:
{
  "period": "today" | "yesterday" | "week" | "all" | "days",
  "days": number of days (1 for today, 7 for week, 30 for all, etc.),
  "reasoning": "brief explanation"
}

Examples:
- "show today" → {"period": "today", "days": 1}
- "what did I eat today" → {"period": "today", "days": 1}
- "show this week" → {"period": "week", "days": 7}
- "show all records" → {"period": "all", "days": 30}
- "show all my food" → {"period": "all", "days": 30}
- "last 3 days" → {"period": "days", "days": 3}
- "yesterday" → {"period": "yesterday", "days": 1}

Default to "today" if unclear."""

        prompt = f"{system_prompt}\n\nUSER REQUEST: {user_input}\n\nAnalyze what time period they want:"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 150
                        }
                    }
                )
                response.raise_for_status()
                result_data = response.json()

                response_text = result_data.get("response", "{}")
                result = json.loads(response_text)

                logger.info(f"Analyzed report period: {result.get('period')} ({result.get('days')} days)")
                return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse report analysis JSON: {e}")
            return {"period": "today", "days": 1, "reasoning": "Fallback - parse error"}
        except Exception as e:
            logger.error(f"Error analyzing report request with Ollama: {e}")
            return {"period": "today", "days": 1, "reasoning": f"Error: {str(e)}"}

    async def translate_to_english(self, text: str) -> str:
        """
        Translate food name to English for FatSecret search.

        Args:
            text: Food name in any language (Russian, Ukrainian, etc.)

        Returns:
            English translation of the food name
        """
        # If already in English (basic check), return as-is
        if text and all(ord(char) < 128 for char in text if char.isalpha()):
            return text

        prompt = f"""Translate this food name to English. Return ONLY the English translation, nothing else.

Food name: {text}

Rules:
- Return only the English translation
- Keep it simple (e.g., "яйца" → "eggs", "курица" → "chicken")
- If it's a brand name, keep it as-is
- If already in English, return unchanged

English translation:"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_text,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 50
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                translation = result.get("response", "").strip()

                # Clean up the response (remove quotes, extra text)
                translation = translation.replace('"', '').replace("'", '').strip()

                # Take only first line if multiple lines returned
                if '\n' in translation:
                    translation = translation.split('\n')[0].strip()

                logger.info(f"Translated '{text}' → '{translation}'")
                return translation if translation else text

        except Exception as e:
            logger.error(f"Error translating with Ollama: {e}")
            return text  # Return original if translation fails


# Global service instance
ollama_service = OllamaService()
