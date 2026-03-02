"""
Nutrition Marker Detector for quality gating.
Detects nutrition-related keywords in Russian and English text.
"""
import re
from typing import List


class MarkerDetector:
    """
    Detects nutrition markers in OCR text for quality assessment.

    Used to determine if OCR output contains sufficient nutrition-related
    keywords to proceed with parsing or trigger vision fallback.
    """

    # Nutrition markers (case-insensitive patterns)
    MARKERS = {
        'calories': [
            r'ккал',
            r'kcal',
            r'калор',
            r'энергет',
            r'кдж',
            r'kj',
        ],
        'protein': [
            r'белк',
            r'белок',
            r'protein',
            r'протеин',
        ],
        'carbs': [
            r'углевод',
            r'carb',
            r'carbohydrate',
        ],
        'fat': [
            r'жир',
            r'fat',
            r'липид',
        ],
        'fiber': [
            r'клетчатка',
            r'волок',
            r'fiber',
            r'пищевые\s+волокна',
        ],
        'sugar': [
            r'сахар',
            r'sugar',
        ],
        'salt': [
            r'соль',
            r'salt',
        ],
        'sodium': [
            r'натрий',
            r'sodium',
        ],
        'per_100g': [
            r'на\s*100\s*г',
            r'на\s*100г',
            r'per\s*100\s*g',
            r'100\s*г',
            r'100г',
        ],
    }

    def find_markers(self, text: str) -> List[str]:
        """
        Find nutrition markers in text.

        Args:
            text: OCR extracted text

        Returns:
            List of found marker strings (e.g., ['ккал', 'белк', '100 г'])

        Example:
            >>> detector = MarkerDetector()
            >>> text = "Энергетическая ценность 250 ккал Белки 12г на 100г"
            >>> markers = detector.find_markers(text)
            >>> print(markers)
            ['ккал', 'белки', 'на 100г']
        """
        text_lower = text.lower()
        found = []

        for category, patterns in self.MARKERS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    # Add the actual matched text (not the pattern)
                    found.append(match.group(0))
                    break  # Only count one match per category

        # Deduplicate
        unique_markers = list(dict.fromkeys(found))

        return unique_markers

    def count_categories(self, text: str) -> int:
        """
        Count how many nutrition categories are present.

        Args:
            text: OCR extracted text

        Returns:
            Number of distinct nutrition categories found (0-9)

        This is useful for quality gating: if >= 2 categories found,
        OCR likely captured enough nutrition info.
        """
        text_lower = text.lower()
        categories_found = 0

        for category, patterns in self.MARKERS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    categories_found += 1
                    break  # Count category only once

        return categories_found
