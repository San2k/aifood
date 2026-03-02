"""
Unit tests for OCR parser.
"""
import pytest
from src.services.ocr_parser import OCRParser


def test_extract_value():
    """Test numeric value extraction from text."""
    # Russian text with comma decimal
    text = "Белок: 12,5г"
    value = OCRParser.extract_value(r'белок[:\s]*(\d+[,.]?\d*)', text)
    assert value == 12.5

    # English text with dot decimal
    text_en = "Protein: 12.5g"
    value = OCRParser.extract_value(r'protein[:\s]*(\d+[,.]?\d*)', text_en)
    assert value == 12.5

    # No match
    value = OCRParser.extract_value(r'жир[:\s]*(\d+[,.]?\d*)', text)
    assert value is None


def test_extract_nutrition_basis():
    """Test nutrition basis extraction."""
    # Per 100g
    text = "Пищевая ценность на 100г"
    basis, serving = OCRParser.extract_nutrition_basis(text)
    assert basis == 'per_100g'
    assert serving is None

    # Per serving
    text_serving = "На порцию 150г"
    basis, serving = OCRParser.extract_nutrition_basis(text_serving)
    assert basis == 'per_serving'
    assert serving == 150.0

    # Default to per_100g if not specified
    text_unknown = "Калорийность 250 ккал"
    basis, serving = OCRParser.extract_nutrition_basis(text_unknown)
    assert basis == 'per_100g'


def test_extract_product_info():
    """Test product name and brand extraction."""
    text_lines = [
        {'text': 'Овсяное печенье', 'confidence': 0.95},
        {'text': 'BrandName', 'confidence': 0.92},
        {'text': 'Калории 250 ккал', 'confidence': 0.88}
    ]

    info = OCRParser.extract_product_info(text_lines)
    assert info['product_name'] == 'Овсяное печенье'
    assert info['brand'] == 'BrandName'


def test_parse_nutrition_from_ocr():
    """Test full nutrition parsing from OCR lines."""
    text_lines = [
        {'text': 'Овсяное печенье', 'confidence': 0.95},
        {'text': 'Энергетическая ценность 250 ккал', 'confidence': 0.90},
        {'text': 'Белки 12г', 'confidence': 0.88},
        {'text': 'Углеводы 30г', 'confidence': 0.87},
        {'text': 'Жиры 10г', 'confidence': 0.89},
        {'text': 'на 100г', 'confidence': 0.92}
    ]

    result = OCRParser.parse_nutrition_from_ocr(text_lines)

    assert result['product_name'] == 'Овсяное печенье'
    assert result['nutrition_basis'] == 'per_100g'
    assert result['nutrition_per_100g']['calories_kcal'] == 250
    assert result['nutrition_per_100g']['protein_g'] == 12
    assert result['nutrition_per_100g']['carbs_g'] == 30
    assert result['nutrition_per_100g']['fat_g'] == 10


def test_parse_nutrition_missing_calories():
    """Test parsing fails when calories are missing."""
    text_lines = [
        {'text': 'Овсяное печенье', 'confidence': 0.95},
        {'text': 'Белки 12г', 'confidence': 0.88},
        {'text': 'Углеводы 30г', 'confidence': 0.87}
    ]

    with pytest.raises(ValueError, match="Could not extract calories"):
        OCRParser.parse_nutrition_from_ocr(text_lines)


def test_parse_nutrition_per_serving():
    """Test parsing with per-serving basis."""
    text_lines = [
        {'text': 'Протеиновый батончик', 'confidence': 0.95},
        {'text': 'На порцию 50г', 'confidence': 0.92},
        {'text': 'Калории 125 ккал', 'confidence': 0.90},
        {'text': 'Белок 6г', 'confidence': 0.88}
    ]

    result = OCRParser.parse_nutrition_from_ocr(text_lines)

    assert result['nutrition_basis'] == 'per_serving'
    assert result['serving_size_g'] == 50.0
    assert result['nutrition_per_100g']['calories_kcal'] == 125  # Not converted yet
    assert result['nutrition_per_100g']['protein_g'] == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
