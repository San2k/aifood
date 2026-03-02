"""
Validate and normalize nutrition data.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from ...services.validation import NutritionValidator

logger = logging.getLogger(__name__)


async def validate_nutrition(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply validation rules:
    - Comma → dot conversion
    - kJ → kcal detection
    - Per-serving → per-100g normalization
    - Range checks (calories 0-900, macros 0-100, sum <= 120)

    Args:
        state: LabelProcessingState with nutrition_per_100g

    Returns:
        Updated state with validated nutrition_per_100g
    """
    scan_id = state["scan_id"]
    nutrition = state.get("nutrition_per_100g")
    basis = state.get("nutrition_basis", "per_100g")
    serving_size_g = state.get("serving_size_g")

    logger.info(f"[{scan_id}] Validating nutrition data")

    # Check if previous step failed
    if state.get("should_end") or nutrition is None:
        logger.error(f"[{scan_id}] Cannot validate: nutrition data is missing")
        return {
            **state,
            "status": "failed",
            "error_message": "Nutrition data missing from extraction step",
            "should_end": True,
        }

    try:
        validator = NutritionValidator()

        # 1. Normalize to per_100g if needed
        if basis == "per_serving":
            logger.info(f"[{scan_id}] Converting per_serving ({serving_size_g}g) → per_100g")
            nutrition = validator.normalize_to_per_100g(nutrition, basis, serving_size_g)
            basis = "per_100g"

        # 2. Detect kJ mislabeled as kcal
        if "calories_kcal" in nutrition and "calories_kj" in nutrition:
            corrected, was_corrected = validator.detect_kj_mislabeled_as_kcal(
                nutrition.get("calories_kcal"),
                nutrition.get("calories_kj")
            )
            if was_corrected:
                logger.warning(f"[{scan_id}] Corrected kJ mislabeled as kcal: {corrected}")
                nutrition["calories_kcal"] = corrected

        # 3. Validate ranges
        errors = validator.validate_nutrition_per_100g(nutrition)
        if errors:
            error_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            logger.error(f"[{scan_id}] Validation errors: {error_msg}")
            return {
                **state,
                "status": "failed",
                "error_message": f"Nutrition validation failed: {error_msg}",
                "should_end": True,
            }

        logger.info(f"[{scan_id}] Validation passed")

        return {
            **state,
            "nutrition_per_100g": nutrition,
            "nutrition_basis": basis,
            "current_step": "validate_nutrition",
            "progress": 70,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"[{scan_id}] Validation error: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Validation error: {str(e)}",
            "should_end": True,
        }
