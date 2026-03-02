"""
Parse nutrition data from OCR text using regex patterns.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from ...services.ocr_parser import OCRParser

logger = logging.getLogger(__name__)


async def parse_ocr_nutrition(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured nutrition data from OCR text lines using regex.

    Args:
        state: LabelProcessingState with ocr_text_lines

    Returns:
        Updated state with product_name, nutrition_per_100g, etc.
    """
    scan_id = state["scan_id"]
    text_lines = state["ocr_text_lines"]

    logger.info(f"[{scan_id}] Parsing nutrition from {len(text_lines)} OCR lines")

    try:
        result = OCRParser.parse_nutrition_from_ocr(text_lines)

        logger.info(
            f"[{scan_id}] Parsed: {result['product_name']}, "
            f"basis={result['nutrition_basis']}, "
            f"calories={result['nutrition_per_100g'].get('calories_kcal', 0)} kcal"
        )

        return {
            **state,
            "product_name": result["product_name"],
            "brand": result.get("brand"),
            "nutrition_basis": result["nutrition_basis"],
            "serving_size_g": result.get("serving_size_g"),
            "nutrition_per_100g": result["nutrition_per_100g"],
            "ingredients": result.get("ingredients"),
            "allergens": result.get("allergens"),
            "extraction_method": "paddleocr",
            "confidence": state["ocr_global_confidence"],
            "current_step": "parse_ocr_nutrition",
            "progress": 60,
            "updated_at": datetime.utcnow(),
        }

    except ValueError as e:
        # Parsing failed (e.g., missing calories) → fallback to vision
        logger.warning(f"[{scan_id}] Parsing failed: {e} → vision_fallback")
        return {
            **state,
            "next_node": "vision_fallback",
            "notes": f"OCR parsing failed: {str(e)}",
            "current_step": "parse_ocr_nutrition",
            "progress": 60,
            "updated_at": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"[{scan_id}] Unexpected parsing error: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Parsing error: {str(e)}",
            "should_end": True,
        }
