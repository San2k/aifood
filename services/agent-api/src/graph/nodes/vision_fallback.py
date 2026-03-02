"""
Fallback to Gemini Vision when OCR quality is insufficient.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from ...services.vision_service import VisionService

logger = logging.getLogger(__name__)


async def vision_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini Vision to extract nutrition data when OCR fails.

    Args:
        state: LabelProcessingState with preprocessed_image_path

    Returns:
        Updated state with product_name, nutrition_per_100g, etc.
    """
    scan_id = state["scan_id"]
    image_path = state["preprocessed_image_path"]

    logger.info(f"[{scan_id}] Using Gemini Vision fallback")

    try:
        vision_service = VisionService()

        # Read image as base64
        import base64
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')

        # Call Gemini Vision
        result = await vision_service.parse_nutrition_label(image_base64)

        logger.info(f"[{scan_id}] Vision result: {result}")

        # Check if result has required fields
        if not result or "error" in result:
            error_msg = result.get("error", "Vision service returned empty result")
            logger.error(f"[{scan_id}] Vision service error: {error_msg}")
            return {
                **state,
                "status": "failed",
                "error_message": f"Vision service failed: {error_msg}",
                "should_end": True,
            }

        # Extract data from result
        product_name = result.get("product_name")
        nutrition_per_100g = result.get("nutrition_per_100g")

        if not product_name or not nutrition_per_100g:
            logger.error(f"[{scan_id}] Vision result missing required fields: product_name or nutrition_per_100g")
            return {
                **state,
                "status": "failed",
                "error_message": "Vision extraction incomplete",
                "should_end": True,
            }

        logger.info(
            f"[{scan_id}] Vision extraction complete: {product_name}, "
            f"confidence={result.get('confidence', 0):.2f}"
        )

        return {
            **state,
            "product_name": product_name,
            "brand": result.get("brand"),
            "nutrition_basis": result.get("nutrition_basis", "per_100g"),
            "serving_size_g": result.get("serving_size_g"),
            "nutrition_per_100g": nutrition_per_100g,
            "ingredients": result.get("ingredients"),
            "allergens": result.get("allergens"),
            "extraction_method": "gemini",
            "confidence": result.get("confidence", 0.5),
            "current_step": "vision_fallback",
            "progress": 60,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"[{scan_id}] Vision fallback failed: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Vision fallback failed: {str(e)}",
            "should_end": True,
        }
