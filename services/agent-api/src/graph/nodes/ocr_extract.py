"""
Extract text from image using OCR service.
"""
import logging
import base64
from typing import Dict, Any
from datetime import datetime
from ...services.ocr_client import OCRClient

logger = logging.getLogger(__name__)


async def ocr_extract(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call ocr-service to extract text from preprocessed image.

    Args:
        state: LabelProcessingState with preprocessed_image_path

    Returns:
        Updated state with ocr_text_lines, ocr_global_confidence, markers_found
    """
    scan_id = state["scan_id"]
    image_path = state["preprocessed_image_path"]

    logger.info(f"[{scan_id}] Extracting text with OCR from {image_path}")

    try:
        # Read image and encode to base64
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        ocr_client = OCRClient()
        result = await ocr_client.process_image(image_base64)

        logger.info(
            f"[{scan_id}] OCR complete: "
            f"confidence={result['global_confidence']:.2f}, "
            f"lines={len(result['text_lines'])}, "
            f"markers={result['markers_found']}"
        )

        return {
            **state,
            "ocr_raw_output": result,
            "ocr_text_lines": result["text_lines"],
            "ocr_global_confidence": result["global_confidence"],
            "markers_found": result["markers_found"],
            "current_step": "ocr_extract",
            "progress": 40,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"[{scan_id}] OCR extraction failed: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"OCR extraction failed: {str(e)}",
            "should_end": True,
        }
