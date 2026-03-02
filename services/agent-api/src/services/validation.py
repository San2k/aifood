"""
Nutrition data validation and normalization utilities.
"""
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NutritionValidator:
    """
    Validator for nutrition data with sanity checks.

    Performs:
    - Range validation (calories, macros)
    - Comma → dot conversion
    - kJ → kcal conversion
    - Macro sum validation
    - Per-serving → per-100g conversion
    """

    @staticmethod
    def comma_to_dot(value: Any) -> Optional[Decimal]:
        """
        Convert European decimal notation (comma) to dot.

        Args:
            value: Input value (str, int, float, or Decimal)

        Returns:
            Decimal or None if conversion fails

        Examples:
            >>> NutritionValidator.comma_to_dot("12,5")
            Decimal('12.5')
            >>> NutritionValidator.comma_to_dot("1 234,56")
            Decimal('1234.56')
        """
        if value is None:
            return None

        try:
            if isinstance(value, str):
                # Remove spaces and replace comma with dot
                value = value.replace(' ', '').replace(',', '.')
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Failed to convert value '{value}' to Decimal: {e}")
            return None

    @staticmethod
    def kj_to_kcal(kj: float) -> float:
        """
        Convert kilojoules to kilocalories.

        Args:
            kj: Energy in kilojoules

        Returns:
            Energy in kilocalories

        Formula: 1 kcal = 4.184 kJ
        """
        return round(kj / 4.184, 1)

    @staticmethod
    def validate_range(
        value: Optional[Decimal],
        min_val: float,
        max_val: float,
        field_name: str
    ) -> bool:
        """
        Validate value is within range.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Field name for logging

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # Null values are allowed for optional fields

        value_float = float(value)

        if not (min_val <= value_float <= max_val):
            logger.warning(
                f"{field_name} value {value_float} out of range "
                f"[{min_val}, {max_val}]"
            )
            return False

        return True

    @staticmethod
    def validate_nutrition_per_100g(nutrition: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate nutrition values per 100g.

        Args:
            nutrition: Dictionary with nutrition values

        Returns:
            Dict with validation errors (empty if valid)

        Example:
            >>> validator = NutritionValidator()
            >>> errors = validator.validate_nutrition_per_100g({
            ...     'calories_kcal': 250,
            ...     'protein_g': 12,
            ...     'carbs_g': 30,
            ...     'fat_g': 10
            ... })
            >>> print(errors)
            {}
        """
        errors = {}

        # Calories: 0-900 kcal per 100g
        if 'calories_kcal' in nutrition:
            cal = nutrition['calories_kcal']
            if cal is not None:
                cal_float = float(cal)
                if not (0 <= cal_float <= 900):
                    errors['calories_kcal'] = f"Calories {cal_float} out of range [0, 900]"

        # Protein: 0-100g per 100g
        if 'protein_g' in nutrition:
            protein = nutrition['protein_g']
            if protein is not None and not (0 <= float(protein) <= 100):
                errors['protein_g'] = f"Protein {protein} out of range [0, 100]"

        # Carbs: 0-100g per 100g
        if 'carbs_g' in nutrition:
            carbs = nutrition['carbs_g']
            if carbs is not None and not (0 <= float(carbs) <= 100):
                errors['carbs_g'] = f"Carbs {carbs} out of range [0, 100]"

        # Fat: 0-100g per 100g
        if 'fat_g' in nutrition:
            fat = nutrition['fat_g']
            if fat is not None and not (0 <= float(fat) <= 100):
                errors['fat_g'] = f"Fat {fat} out of range [0, 100]"

        # Fiber: 0-50g per 100g
        if 'fiber_g' in nutrition:
            fiber = nutrition['fiber_g']
            if fiber is not None and not (0 <= float(fiber) <= 50):
                errors['fiber_g'] = f"Fiber {fiber} out of range [0, 50]"

        # Macro sum check: protein + carbs + fat ≤ 120g
        protein = float(nutrition.get('protein_g') or 0)
        carbs = float(nutrition.get('carbs_g') or 0)
        fat = float(nutrition.get('fat_g') or 0)
        macro_sum = protein + carbs + fat

        if macro_sum > 120:
            errors['macro_sum'] = f"Macro sum {macro_sum:.1f}g exceeds 120g per 100g"

        return errors

    @staticmethod
    def normalize_to_per_100g(
        nutrition: Dict[str, Any],
        basis: str,
        serving_size_g: Optional[float]
    ) -> Dict[str, Any]:
        """
        Normalize nutrition values to per 100g.

        Args:
            nutrition: Nutrition values
            basis: 'per_100g' or 'per_serving'
            serving_size_g: Serving size in grams (required if basis='per_serving')

        Returns:
            Normalized nutrition dict (always per 100g)

        Raises:
            ValueError: If basis is per_serving but serving_size_g is missing
        """
        if basis == 'per_100g':
            return nutrition

        if basis == 'per_serving':
            if not serving_size_g or serving_size_g <= 0:
                raise ValueError(
                    f"Cannot normalize per_serving without valid serving_size_g "
                    f"(got: {serving_size_g})"
                )

            multiplier = 100.0 / serving_size_g

            normalized = {}
            for key, value in nutrition.items():
                if value is not None:
                    normalized[key] = round(float(value) * multiplier, 1)
                else:
                    normalized[key] = None

            logger.info(
                f"Converted from per_serving ({serving_size_g}g) to per_100g "
                f"(multiplier: {multiplier:.2f})"
            )

            return normalized

        raise ValueError(f"Unknown nutrition_basis: {basis}")

    @staticmethod
    def detect_kj_mislabeled_as_kcal(
        calories_kcal: Optional[float],
        kj: Optional[float]
    ) -> tuple[float, bool]:
        """
        Detect if kJ was mislabeled as kcal.

        If calories_kcal > 900 and kj is provided, likely kJ was mislabeled.

        Args:
            calories_kcal: Calories value (possibly kJ)
            kj: Kilojoules value

        Returns:
            Tuple of (corrected_kcal, was_corrected)

        Example:
            >>> NutritionValidator.detect_kj_mislabeled_as_kcal(1500, 1500)
            (358.5, True)  # Converted from kJ
        """
        if not calories_kcal:
            if kj:
                # Only kJ provided
                return (NutritionValidator.kj_to_kcal(kj), True)
            return (None, False)

        # If kcal > 900, likely it's kJ mislabeled
        if calories_kcal > 900:
            if kj and abs(calories_kcal - kj) < 100:
                # kcal and kJ are similar → kcal is actually kJ
                corrected = NutritionValidator.kj_to_kcal(calories_kcal)
                logger.warning(
                    f"Detected kJ mislabeled as kcal: {calories_kcal} → {corrected} kcal"
                )
                return (corrected, True)

        return (calories_kcal, False)

    @staticmethod
    def apply_all_normalizations(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all normalization steps to nutrition data.

        Steps:
        1. Comma → dot conversion
        2. kJ → kcal detection/conversion
        3. Per-serving → per-100g conversion
        4. Range validation

        Args:
            data: Raw nutrition data with:
                - nutrition_basis: 'per_100g' | 'per_serving'
                - serving_size_g: float (if per_serving)
                - nutrition_per_100g: dict with nutrition values

        Returns:
            Normalized and validated data

        Raises:
            ValueError: If validation fails
        """
        result = data.copy()

        # 1. Comma → dot for all nutrition values
        if 'nutrition_per_100g' in result:
            nutrition = result['nutrition_per_100g']

            for key in ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g',
                       'fiber_g', 'sugar_g', 'salt_g', 'sodium_mg', 'kj']:
                if key in nutrition and nutrition[key] is not None:
                    nutrition[key] = NutritionValidator.comma_to_dot(nutrition[key])

        # 2. kJ → kcal conversion
        nutrition = result.get('nutrition_per_100g', {})
        calories = nutrition.get('calories_kcal')
        kj = nutrition.get('kj')

        corrected_cal, was_corrected = NutritionValidator.detect_kj_mislabeled_as_kcal(
            float(calories) if calories else None,
            float(kj) if kj else None
        )

        if was_corrected and corrected_cal:
            nutrition['calories_kcal'] = Decimal(str(corrected_cal))
            if 'notes' not in result:
                result['notes'] = []
            if isinstance(result['notes'], str):
                result['notes'] = [result['notes']]
            result['notes'].append(f"Converted from kJ: {kj or calories} → {corrected_cal} kcal")

        # 3. Normalize to per_100g
        if result.get('nutrition_basis') == 'per_serving':
            nutrition = NutritionValidator.normalize_to_per_100g(
                result['nutrition_per_100g'],
                result['nutrition_basis'],
                result.get('serving_size_g')
            )
            result['nutrition_per_100g'] = nutrition
            result['nutrition_basis'] = 'per_100g'  # Update after conversion

        # 4. Validate ranges
        errors = NutritionValidator.validate_nutrition_per_100g(
            result['nutrition_per_100g']
        )

        if errors:
            error_msg = '; '.join([f"{k}: {v}" for k, v in errors.items()])
            raise ValueError(f"Nutrition validation failed: {error_msg}")

        return result


# Global instance
nutrition_validator = NutritionValidator()
