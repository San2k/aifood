"""
Gemini Vision service for nutrition label extraction.
Used as fallback when PaddleOCR confidence is low.
"""
import google.generativeai as genai
import logging
import json
import base64
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)


class VisionService:
    """
    Gemini Vision API client for nutrition label parsing.

    Uses structured JSON output to extract nutrition data from label photos
    when OCR confidence is insufficient.
    """

    def __init__(self):
        """Initialize Gemini Vision service."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured - vision fallback will not work")
            self.configured = False
            return

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.configured = True
            logger.info(f"Gemini Vision service initialized with model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}", exc_info=True)
            self.configured = False

    async def parse_nutrition_label(
        self,
        image_base64: str,
        language: str = "ru"
    ) -> Dict[str, Any]:
        """
        Parse nutrition label using Gemini Vision.

        Args:
            image_base64: Base64-encoded image data
            language: Label language ('ru' for Russian, 'en' for English)

        Returns:
            Dict with:
            - product_name: str
            - brand: str | null
            - nutrition_basis: 'per_100g' | 'per_serving'
            - serving_size_g: float | null
            - nutrition_per_100g: {calories_kcal, protein_g, carbs_g, fat_g, ...}
            - ingredients: str | null
            - allergens: str | null
            - confidence: float (0.0-1.0)
            - extraction_method: 'gemini'
            - notes: str | null
            - error: str (if failed)

        Example:
            >>> service = VisionService()
            >>> result = await service.parse_nutrition_label(image_base64)
            >>> print(result['product_name'])
            'Овсяное печенье'
        """
        if not self.configured:
            return {
                "error": "Gemini Vision service not configured (missing GEMINI_API_KEY)"
            }

        try:
            logger.info("Processing nutrition label with Gemini Vision API")

            # Construct prompt for Russian nutrition labels
            prompt = self._build_prompt(language)

            # Prepare image for Gemini
            image_data = base64.b64decode(image_base64)

            # Call Gemini Vision API
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ])

            # Parse JSON response
            try:
                result = json.loads(response.text)
                logger.info(f"Gemini extracted: {result.get('product_name')} ({result.get('brand')})")

                # Add extraction metadata
                result['extraction_method'] = 'gemini'

                # Validate and normalize
                result = self._normalize_result(result)

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.debug(f"Raw response: {response.text[:500]}")
                return {
                    "error": f"Gemini returned invalid JSON: {str(e)}",
                    "raw_response": response.text[:500]
                }

        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}", exc_info=True)
            return {
                "error": f"Vision processing failed: {str(e)}"
            }

    def _build_prompt(self, language: str) -> str:
        """
        Build prompt for Gemini Vision API.

        Args:
            language: Label language

        Returns:
            Formatted prompt string
        """
        if language == "ru":
            lang_instructions = """
This is a RUSSIAN food product nutrition label.
Read the text carefully - it may contain Cyrillic characters.
"""
        else:
            lang_instructions = "This is a food product nutrition label."

        prompt = f"""{lang_instructions}

Extract EXACT nutrition data from this label and return ONLY valid JSON (no markdown, no extra text).

OUTPUT JSON SCHEMA:
{{
  "product_name": "exact product name from label",
  "brand": "brand name or null",
  "nutrition_basis": "per_100g" or "per_serving",
  "serving_size_g": number or null,
  "nutrition_per_100g": {{
    "calories_kcal": number,
    "protein_g": number or null,
    "carbs_g": number or null,
    "fat_g": number or null,
    "fiber_g": number or null,
    "sugar_g": number or null,
    "salt_g": number or null,
    "sodium_mg": number or null,
    "kj": number or null
  }},
  "ingredients": "ingredients text or null",
  "allergens": "allergens text or null",
  "confidence": 0.0 to 1.0,
  "notes": "any warnings or observations"
}}

CRITICAL RULES:
1. READ printed numbers EXACTLY - do NOT calculate or hallucinate
2. If label shows "на 100г" or "per 100g": nutrition_basis = "per_100g"
3. If label shows "на порцию Xг" or "per serving Xg": nutrition_basis = "per_serving", serving_size_g = X
4. ALL nutrition values must be converted to per_100g:
   - If per_serving: multiply/divide to get per 100g
   - Formula: value_per_100g = (value_per_serving / serving_size_g) * 100
5. Decimal separator: Convert commas to dots ("12,5" → 12.5)
6. Energy units:
   - If only kJ shown (no kcal): calories_kcal = kj / 4.184
   - Store both if available
7. Confidence scoring:
   - 0.9-1.0: Clear, well-printed label
   - 0.7-0.9: Readable but some unclear parts
   - 0.5-0.7: Blurry or damaged label
   - <0.5: Very poor quality
8. Return ONLY the JSON object, no extra text, no markdown code blocks

VALIDATION:
- calories_kcal: 0-900 per 100g (if higher, likely kJ mislabeled)
- protein_g, carbs_g, fat_g: 0-100 per 100g each
- protein_g + carbs_g + fat_g should be ≤ 120g per 100g
- If values seem wrong, note it in "notes" field

Remember: READ EXACT VALUES, do not invent or estimate nutrition data.
"""
        return prompt

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate Gemini result.

        Args:
            result: Raw Gemini response

        Returns:
            Normalized result with validation
        """
        # Ensure nutrition_per_100g exists
        if 'nutrition_per_100g' not in result:
            result['nutrition_per_100g'] = {}

        nutrition = result['nutrition_per_100g']

        # Convert to per_100g if needed
        if result.get('nutrition_basis') == 'per_serving' and result.get('serving_size_g'):
            serving_size = float(result['serving_size_g'])
            multiplier = 100.0 / serving_size

            for key in ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g',
                       'fiber_g', 'sugar_g', 'salt_g', 'sodium_mg']:
                if key in nutrition and nutrition[key] is not None:
                    nutrition[key] = round(float(nutrition[key]) * multiplier, 1)

            # Update basis after conversion
            result['nutrition_basis'] = 'per_100g'
            logger.debug(f"Converted from per_serving ({serving_size}g) to per_100g")

        # kJ → kcal conversion if needed
        if nutrition.get('kj') and not nutrition.get('calories_kcal'):
            nutrition['calories_kcal'] = round(float(nutrition['kj']) / 4.184, 1)
            logger.debug(f"Converted {nutrition['kj']} kJ to {nutrition['calories_kcal']} kcal")

        # Validate ranges and add warnings to notes
        warnings = []

        if nutrition.get('calories_kcal'):
            cal = float(nutrition['calories_kcal'])
            if cal > 900:
                warnings.append(f"Calories {cal} exceeds 900 kcal/100g (possibly kJ)")
            elif cal < 0:
                warnings.append("Negative calories detected")

        # Macro sum check
        protein = float(nutrition.get('protein_g') or 0)
        carbs = float(nutrition.get('carbs_g') or 0)
        fat = float(nutrition.get('fat_g') or 0)
        macro_sum = protein + carbs + fat

        if macro_sum > 120:
            warnings.append(f"Macro sum {macro_sum:.1f}g exceeds 120g/100g")

        # Add warnings to notes
        if warnings:
            existing_notes = result.get('notes', '')
            result['notes'] = '; '.join(warnings) + (f'; {existing_notes}' if existing_notes else '')

        # Ensure confidence is set
        if 'confidence' not in result or result['confidence'] is None:
            result['confidence'] = 0.8  # Default for Gemini

        return result


# Global instance
vision_service = VisionService()
