"""
OCR text parser for nutrition label extraction.
Uses regex patterns to extract nutrition data from Russian text.
"""
import re
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class OCRParser:
    """
    Parser for extracting nutrition data from OCR text.

    Supports Russian and English patterns for:
    - Product name and brand
    - Calories (kcal, kJ)
    - Macronutrients (protein, carbs, fat)
    - Fiber, sugar, salt, sodium
    - Nutrition basis (per 100g or per serving)
    """

    # Regex patterns for nutrition extraction
    PATTERNS = {
        # Calories
        'calories': [
            r'(?:калор|энергия|energy|ккал|kcal)[:\s]*(\d+[,.]?\d*)',
            r'энергетическая\s+ценность[:\s]*(\d+[,.]?\d*)',
        ],
        'kj': [
            r'(?:кдж|kj)[:\s]*(\d+[,.]?\d*)',
        ],

        # Protein
        'protein': [
            r'(?:белк|белок|protein|протеин)[:\s]*(\d+[,.]?\d*)',
        ],

        # Carbohydrates
        'carbs': [
            r'(?:углевод|carb|carbohydrate)[:\s]*(\d+[,.]?\d*)',
        ],

        # Fat
        'fat': [
            r'(?:жир|fat|липид)[:\s]*(\d+[,.]?\d*)',
        ],

        # Fiber
        'fiber': [
            r'(?:клетчатка|пищевые\s+волокна|волок|fiber|dietary\s+fiber)[:\s]*(\d+[,.]?\d*)',
        ],

        # Sugar
        'sugar': [
            r'(?:сахар|sugar)(?:\s+в\s+т\.ч\.)?[:\s]*(\d+[,.]?\d*)',
            r'(?:в\s+т\.ч\.\s+)?сахар[:\s]*(\d+[,.]?\d*)',
        ],

        # Salt
        'salt': [
            r'(?:соль|salt)[:\s]*(\d+[,.]?\d*)',
        ],

        # Sodium
        'sodium': [
            r'(?:натрий|sodium)[:\s]*(\d+[,.]?\d*)',
        ],

        # Nutrition basis
        'per_100g': [
            r'на\s*100\s*г',
            r'на\s*100г',
            r'per\s*100\s*g',
            r'100\s*г',
        ],
        'per_serving': [
            r'на\s*(?:порцию|serving)\s*(?::|-)?\s*(\d+)\s*г',
            r'порция[:\s]*(\d+)\s*г',
        ],
    }

    @staticmethod
    def extract_value(pattern: str, text: str) -> Optional[float]:
        """
        Extract numeric value using regex pattern.

        Args:
            pattern: Regex pattern to match
            text: Text to search

        Returns:
            Extracted float value or None

        Example:
            >>> OCRParser.extract_value(r'белок[:\s]*(\d+[,.]?\d*)', 'Белок: 12,5г')
            12.5
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '.')
            try:
                return float(value_str)
            except ValueError:
                logger.warning(f"Failed to convert '{value_str}' to float")
                return None
        return None

    @staticmethod
    def extract_nutrition_basis(text: str) -> tuple[str, Optional[float]]:
        """
        Extract nutrition basis (per 100g or per serving).

        Args:
            text: OCR text

        Returns:
            Tuple of (basis, serving_size_g)
            - basis: 'per_100g' or 'per_serving'
            - serving_size_g: serving size in grams (if per_serving)

        Example:
            >>> OCRParser.extract_nutrition_basis('Пищевая ценность на 100г')
            ('per_100g', None)
            >>> OCRParser.extract_nutrition_basis('На порцию 150г')
            ('per_serving', 150.0)
        """
        text_lower = text.lower()

        # Check for per_serving first (more specific)
        for pattern in OCRParser.PATTERNS['per_serving']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                serving_size = float(match.group(1))
                logger.debug(f"Found per_serving: {serving_size}g")
                return ('per_serving', serving_size)

        # Check for per_100g
        for pattern in OCRParser.PATTERNS['per_100g']:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.debug("Found per_100g basis")
                return ('per_100g', None)

        # Default to per_100g if not specified
        logger.debug("No basis found, defaulting to per_100g")
        return ('per_100g', None)

    @staticmethod
    def extract_product_info(text_lines: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """
        Extract product name and brand from OCR text lines.

        Args:
            text_lines: List of OCR text lines with confidence scores

        Returns:
            Dict with 'product_name' and 'brand'

        Heuristic:
        - Product name: first high-confidence line (conf > 0.8)
        - Brand: second high-confidence short line (< 30 chars)
        """
        product_name = None
        brand = None

        for line in text_lines[:5]:  # Check first 5 lines
            text = line.get('text', '')
            confidence = line.get('confidence', 0)

            if confidence > 0.8 and len(text) > 3:
                if not product_name:
                    product_name = text
                elif not brand and len(text) < 30:
                    brand = text
                    break

        if not product_name:
            product_name = "Продукт с этикетки"

        return {
            'product_name': product_name,
            'brand': brand
        }

    @staticmethod
    def parse_nutrition_from_ocr(
        text_lines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse nutrition data from OCR text lines.

        Args:
            text_lines: List of dicts with 'text' and 'confidence'

        Returns:
            Dict with:
            - product_name: str
            - brand: str | null
            - nutrition_basis: 'per_100g' | 'per_serving'
            - serving_size_g: float | null
            - nutrition_per_100g: dict with nutrition values
            - ingredients: str | null
            - allergens: str | null

        Raises:
            ValueError: If no calories found (minimum required field)

        Example:
            >>> lines = [
            ...     {'text': 'Овсяное печенье', 'confidence': 0.95},
            ...     {'text': 'Калории 250 ккал', 'confidence': 0.90},
            ...     {'text': 'Белки 12г', 'confidence': 0.88}
            ... ]
            >>> result = OCRParser.parse_nutrition_from_ocr(lines)
            >>> print(result['nutrition_per_100g']['calories_kcal'])
            250
        """
        # Concatenate all text with confidence > 0.6
        full_text = " ".join([
            line["text"] for line in text_lines
            if line.get("confidence", 0) > 0.6
        ])

        logger.info(f"Parsing OCR text: {full_text[:200]}...")

        # Extract product name and brand
        product_info = OCRParser.extract_product_info(text_lines)

        # Extract nutrition basis
        nutrition_basis, serving_size_g = OCRParser.extract_nutrition_basis(full_text)

        # Extract nutrition values
        nutrition = {}

        for nutrient, patterns in OCRParser.PATTERNS.items():
            if nutrient in ['per_100g', 'per_serving']:
                continue  # Skip basis patterns

            for pattern in patterns:
                value = OCRParser.extract_value(pattern, full_text)
                if value is not None:
                    nutrition[f'{nutrient}{"_g" if nutrient not in ["calories", "kj", "sodium"] else ("_kcal" if nutrient == "calories" else ("_mg" if nutrient == "sodium" else ""))}'] = value
                    break

        # Rename 'calories' to 'calories_kcal' if needed
        if 'calories' in nutrition:
            nutrition['calories_kcal'] = nutrition.pop('calories')

        # Validate: calories is required
        if 'calories_kcal' not in nutrition or nutrition['calories_kcal'] is None:
            raise ValueError("Could not extract calories from OCR text")

        # Extract ingredients (usually at bottom, long text)
        ingredients_match = re.search(
            r'(?:состав|ingredients|ингредиенты)[:\s]*(.*?)(?:аллергены|allergens|$)',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        ingredients = ingredients_match.group(1).strip() if ingredients_match else None

        # Extract allergens
        allergens_match = re.search(
            r'(?:аллергены|allergens|contains)[:\s]*(.*?)$',
            full_text,
            re.IGNORECASE
        )
        allergens = allergens_match.group(1).strip() if allergens_match else None

        result = {
            'product_name': product_info['product_name'],
            'brand': product_info['brand'],
            'nutrition_basis': nutrition_basis,
            'serving_size_g': serving_size_g,
            'nutrition_per_100g': nutrition,
            'ingredients': ingredients,
            'allergens': allergens,
        }

        logger.info(
            f"Extracted: {result['product_name']} ({result['brand']}) - "
            f"Calories: {nutrition.get('calories_kcal')}, "
            f"P: {nutrition.get('protein_g')}, "
            f"C: {nutrition.get('carbs_g')}, "
            f"F: {nutrition.get('fat_g')}"
        )

        return result


# Global instance
ocr_parser = OCRParser()
