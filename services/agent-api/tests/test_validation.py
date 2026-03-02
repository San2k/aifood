"""
Unit tests for nutrition validation.
"""
import pytest
from decimal import Decimal
from src.services.validation import NutritionValidator


def test_comma_to_dot():
    """Test comma to dot conversion."""
    validator = NutritionValidator()

    assert validator.comma_to_dot("12,5") == Decimal("12.5")
    assert validator.comma_to_dot("1 234,56") == Decimal("1234.56")
    assert validator.comma_to_dot("100") == Decimal("100")
    assert validator.comma_to_dot(12.5) == Decimal("12.5")
    assert validator.comma_to_dot(None) is None


def test_kj_to_kcal():
    """Test kJ to kcal conversion."""
    assert NutritionValidator.kj_to_kcal(1000) == 239.0
    assert NutritionValidator.kj_to_kcal(418.4) == 100.0


def test_validate_nutrition_per_100g():
    """Test nutrition validation."""
    validator = NutritionValidator()

    # Valid nutrition
    nutrition = {
        'calories_kcal': 250,
        'protein_g': 12,
        'carbs_g': 30,
        'fat_g': 10
    }
    errors = validator.validate_nutrition_per_100g(nutrition)
    assert len(errors) == 0

    # Invalid: calories too high
    nutrition_invalid = {
        'calories_kcal': 1500,
        'protein_g': 12
    }
    errors = validator.validate_nutrition_per_100g(nutrition_invalid)
    assert 'calories_kcal' in errors

    # Invalid: macro sum > 120
    nutrition_invalid2 = {
        'protein_g': 50,
        'carbs_g': 50,
        'fat_g': 50
    }
    errors = validator.validate_nutrition_per_100g(nutrition_invalid2)
    assert 'macro_sum' in errors


def test_normalize_to_per_100g():
    """Test per-serving to per-100g conversion."""
    validator = NutritionValidator()

    # Per 100g (no conversion needed)
    nutrition = {'calories_kcal': 250, 'protein_g': 12}
    result = validator.normalize_to_per_100g(nutrition, 'per_100g', None)
    assert result['calories_kcal'] == 250

    # Per serving (convert to per 100g)
    nutrition_serving = {'calories_kcal': 125, 'protein_g': 6}  # Per 50g
    result = validator.normalize_to_per_100g(nutrition_serving, 'per_serving', 50)
    assert result['calories_kcal'] == 250.0  # 125 * (100/50) = 250
    assert result['protein_g'] == 12.0  # 6 * 2 = 12

    # Invalid: per_serving without serving_size_g
    with pytest.raises(ValueError):
        validator.normalize_to_per_100g(nutrition_serving, 'per_serving', None)


def test_detect_kj_mislabeled_as_kcal():
    """Test kJ mislabeled as kcal detection."""
    validator = NutritionValidator()

    # kJ mislabeled as kcal
    corrected, was_corrected = validator.detect_kj_mislabeled_as_kcal(1500, 1500)
    assert was_corrected is True
    assert 350 < corrected < 360  # 1500 / 4.184 ≈ 358.5

    # Normal kcal value
    corrected, was_corrected = validator.detect_kj_mislabeled_as_kcal(250, 1046)
    assert was_corrected is False
    assert corrected == 250

    # Only kJ provided
    corrected, was_corrected = validator.detect_kj_mislabeled_as_kcal(None, 1000)
    assert was_corrected is True
    assert corrected == 239.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
