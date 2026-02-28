"""
OpenAI Service for text parsing and Vision OCR.
Handles all interactions with OpenAI API.
"""

import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
import json

from ..config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions."""
    
    def __init__(self):
        # Initialize client only if API key is provided
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
        self.model_text = settings.OPENAI_MODEL_TEXT
        self.model_vision = settings.OPENAI_MODEL_VISION
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    async def parse_food_text(self, user_input: str) -> Dict[str, Any]:
        """
        Parse food text input using GPT-4.
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
- "калорий 250 БЖУ 30/20/10 на 100г" → {calories: 250, protein: 30, fat: 30, carbs: 10, is_per_100g: true}
- "на 100 грамм: калории 350, белки 20, жиры 10, углеводы 40" → {calories: 350, protein: 20, fat: 10, carbs: 40, is_per_100g: true}

When user provides nutrition data:
1. Extract exact values (do NOT calculate anything)
2. Set is_per_100g = true if user says "на 100г" / "per 100g" / "на 100 грамм"
3. Set is_per_100g = false otherwise (values are for total portion)
4. If nutrition provided but weight missing → needs_clarification = true, ask for weight
5. Include all nutrition data in custom_nutrition field

Examples:
Input: "Съел 150 грамм салата с тунцом БЖУ 50/50/50 калорий 150"
Output: {
  "items": [{
    "name": "салата с тунцом",
    "quantity": 150,
    "unit": "g",
    "custom_nutrition": {
      "protein": 50,
      "fat": 50,
      "carbs": 50,
      "calories": 150,
      "is_per_100g": false
    }
  }]
}

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
}

Input: "Салат с тунцом БЖУ 30/20/10 калорий 250 на 100г"
Output: {
  "items": [{
    "name": "Салат с тунцом",
    "quantity": null,
    "unit": "g",
    "custom_nutrition": {
      "protein": 30,
      "fat": 20,
      "carbs": 10,
      "calories": 250,
      "is_per_100g": true
    }
  }],
  "needs_clarification": true,
  "clarification_reasons": ["Weight not specified for custom nutrition"]
}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,  # Lower for more deterministic parsing
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Parsed food text: {len(result.get('items', []))} items found")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing food text: {e}")
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
        Recognize food product from package photo using GPT-4o Vision.
        Extracts product name, brand, and basic info for searching.

        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data (alternative to URL)

        Returns:
            Dict with product name and search query
        """
        system_prompt = """You are a food product recognition specialist.
Look at this food product package and identify what it is.

OUTPUT SCHEMA:
{
  "product_name": "specific product name in original language",
  "brand": "brand name or null",
  "food_type": "general food category (e.g., apple, bread, yogurt)",
  "search_query": "optimized search term for food database",
  "confidence": 0.0-1.0,
  "notes": "any additional details"
}

RULES:
- Extract the exact product name visible on package
- Identify the brand if visible
- Create a search_query that's generic enough to find in food databases
- If package shows serving size or weight, include in notes
- Confidence based on image clarity and text visibility"""

        try:
            # Prepare image content
            if image_data:
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            else:
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }

            response = await self.client.chat.completions.create(
                model=self.model_vision,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Identify this food product from the package. Return valid JSON only."
                            },
                            image_content
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Recognized food from photo: {result.get('product_name', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"Error recognizing food from photo: {e}")
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
        Parse nutrition label from image using GPT-4o Vision.
        
        Args:
            image_url: URL or file path to image
            image_data: Base64 encoded image data (alternative to URL)
            
        Returns:
            Dict with extracted nutrition data
        """
        system_prompt = """You are reading a food nutrition label. Extract the EXACT numbers you see.

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
            # Prepare image content
            if image_data:
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            else:
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            
            response = await self.client.chat.completions.create(
                model=self.model_vision,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract nutrition information from this food label image. Return valid JSON only."
                            },
                            image_content
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Parsed nutrition label: {result.get('product_name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing nutrition label: {e}")
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
        Generate personalized nutrition advice using GPT-4.
        
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

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            advice = response.choices[0].message.content.strip()
            logger.info("Generated nutrition advice")
            return advice
            
        except Exception as e:
            logger.error(f"Error generating advice: {e}")
            return "Unable to generate advice at this time. Please try again later."
    
    async def clarify_food_item(
        self,
        food_name: str,
        context: str = ""
    ) -> List[str]:
        """
        Generate clarification questions for ambiguous food input.
        
        Args:
            food_name: Ambiguous food name
            context: Additional context
            
        Returns:
            List of clarification questions
        """
        prompt = f"""Food item: "{food_name}"
Context: {context}

Generate 1-3 specific clarification questions to determine:
- Exact food item (if ambiguous)
- Cooking method (raw, cooked, fried, etc.)
- Quantity/weight if not specified

Return as JSON array of strings: ["question1", "question2"]
Keep questions brief and clear."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            questions = result.get("questions", [])
            logger.info(f"Generated {len(questions)} clarification questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating clarification: {e}")
            return [f"Could you specify the exact type and quantity of {food_name}?"]

    async def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from natural language input using OpenAI.

        Args:
            user_input: Raw user message

        Returns:
            Dict with intent classification and confidence
        """
        if not self.client:
            return {
                "intent": "food_entry",
                "confidence": 0.5,
                "reasoning": "No OpenAI API key configured"
            }

        system_prompt = """You are an intent classifier for a nutrition tracking bot.
Classify user messages into one of these intents:

1. "food_entry" - User is logging food they ate
2. "view_report" - User wants to see their food log/report
3. "question" - User is asking a nutrition-related question
4. "chat" - Greetings, thanks, small talk

Return JSON with: intent, confidence (0-1), and reasoning."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2,
                max_tokens=150,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Detected intent: {result.get('intent')} (confidence: {result.get('confidence')})")
            return result

        except Exception as e:
            logger.error(f"Error detecting intent with OpenAI: {e}")
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
        Generate a conversational response for questions and chat using OpenAI.

        Args:
            user_input: User's message
            intent: Detected intent (question or chat)
            user_context: Optional user profile and data

        Returns:
            Conversational response text
        """
        if not self.client:
            return "Извините, произошла ошибка. Попробуйте еще раз."

        if intent == "chat":
            system_prompt = """You are a friendly nutrition tracking assistant.
Respond to greetings and small talk warmly and briefly (1-2 sentences).
Always encourage healthy eating habits."""

        elif intent == "question":
            system_prompt = """You are a knowledgeable nutrition assistant.
Answer nutrition questions accurately and helpfully in 2-3 sentences.
Base answers on scientific nutrition facts.
DO NOT provide medical advice - suggest consulting professionals for health issues."""

            if user_context:
                goal = user_context.get('goal', 'maintenance')
                target_cals = user_context.get('target_calories', 2000)
                system_prompt += f"\n\nUser context: Goal={goal}, Target={target_cals} kcal/day"

        elif intent == "view_report":
            return "Для просмотра дневника используйте команды:\n• /today - сегодняшний отчёт\n• /week - недельный отчёт"

        else:
            return "Извините, не понял ваш запрос. Попробуйте переформулировать или используйте /help."

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=250
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated conversational response for intent: {intent}")
            return response_text

        except Exception as e:
            logger.error(f"Error generating conversational response with OpenAI: {e}")
            return "Извините, произошла ошибка. Попробуйте еще раз."

    async def analyze_report_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user's report request to understand what time period they want.

        Args:
            user_input: User's message about viewing reports

        Returns:
            Dict with period type and days count
        """
        if not self.client:
            return {"period": "today", "days": 1, "reasoning": "No OpenAI API key"}

        system_prompt = """You are analyzing a user's request to view their food log.
Determine what time period they want to see.

Return ONLY valid JSON with this structure:
{
  "period": "today" | "yesterday" | "week" | "all" | "days",
  "days": number,
  "reasoning": "brief explanation"
}

Rules:
- "today" or "сегодня" → {"period": "today", "days": 1}
- "yesterday" or "вчера" → {"period": "yesterday", "days": 1}
- "week" or "неделя" or "за неделю" → {"period": "week", "days": 7}
- "all" or "все записи" or "всё" → {"period": "all", "days": 30}
- "last N days" or "за N дней" → {"period": "days", "days": N}

If unclear, default to "today"."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2,
                max_tokens=150,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Analyzed report period with OpenAI: {result.get('period')} ({result.get('days')} days)")
            return result

        except Exception as e:
            logger.error(f"Error analyzing report request with OpenAI: {e}")
            return {
                "period": "today",
                "days": 1,
                "reasoning": f"Error: {str(e)}"
            }

    async def translate_to_english(self, text: str) -> str:
        """
        Translate food name to English for FatSecret search using OpenAI.

        Args:
            text: Food name in any language

        Returns:
            English translation of the food name
        """
        if not self.client:
            return text

        # If already in English (basic check), return as-is
        if text and all(ord(char) < 128 for char in text if char.isalpha()):
            return text

        prompt = f"""Translate this food name to English. Return ONLY the English translation.

Food name: {text}

Return only the English word(s), nothing else."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_text,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=20
            )

            translation = response.choices[0].message.content.strip()
            translation = translation.replace('"', '').replace("'", '').strip()

            logger.info(f"Translated '{text}' → '{translation}' (OpenAI)")
            return translation if translation else text

        except Exception as e:
            logger.error(f"Error translating with OpenAI: {e}")
            return text


# Global service instance
openai_service = OpenAIService()
