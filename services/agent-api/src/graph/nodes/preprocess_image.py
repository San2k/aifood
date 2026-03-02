"""
Preprocess image using OpenCV pipeline.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from ...services.image_preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


async def preprocess_image(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply OpenCV preprocessing: auto-rotate, deskew, CLAHE, upscale.

    Args:
        state: LabelProcessingState with local_image_path

    Returns:
        Updated state with preprocessed_image_path
    """
    scan_id = state.get("scan_id", "unknown")
    local_image_path = state.get("local_image_path")

    # If previous step failed, skip preprocessing
    if state.get("should_end") or local_image_path is None:
        logger.error(f"[{scan_id}] Cannot preprocess: previous step failed")
        return {
            **state,
            "status": "failed",
            "should_end": True,
        }

    logger.info(f"[{scan_id}] Preprocessing image: {local_image_path}")

    try:
        preprocessor = ImagePreprocessor()
        preprocessed_path = preprocessor.preprocess(local_image_path)

        logger.info(f"[{scan_id}] Preprocessing complete: {preprocessed_path}")

        return {
            **state,
            "preprocessed_image_path": preprocessed_path,
            "current_step": "preprocess_image",
            "progress": 20,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"[{scan_id}] Preprocessing failed: {e}", exc_info=True)
        # Continue with original image if preprocessing fails
        logger.warning(f"[{scan_id}] Using original image instead")
        return {
            **state,
            "preprocessed_image_path": local_image_path,
            "current_step": "preprocess_image",
            "progress": 20,
            "notes": f"Preprocessing failed: {str(e)}. Using original image.",
            "updated_at": datetime.utcnow(),
        }
