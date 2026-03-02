"""
Check OCR quality and route to parsing or vision fallback.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from ...config import settings

logger = logging.getLogger(__name__)


async def check_ocr_quality(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quality gate: Check if OCR confidence and markers meet threshold.

    Criteria:
    - OCR confidence >= 0.75
    - At least 2 nutrition markers found

    Args:
        state: LabelProcessingState with ocr_global_confidence and markers_found

    Returns:
        Updated state with next_node routing decision
    """
    scan_id = state.get("scan_id", "unknown")
    confidence = state.get("ocr_global_confidence")
    markers = state.get("markers_found", [])
    text_lines = state.get("ocr_text_lines", [])

    # If previous step failed, skip quality check
    if state.get("should_end") or confidence is None:
        logger.error(f"[{scan_id}] Cannot check quality: previous step failed")
        return {
            **state,
            "status": "failed",
            "should_end": True,
        }

    # ===== DETAILED OCR DEBUG LOGGING =====
    logger.info(f"[{scan_id}] ========== OCR RESULTS DEBUG ==========")
    logger.info(
        f"[{scan_id}] Quality metrics: "
        f"confidence={confidence:.2f} (threshold={settings.OCR_CONFIDENCE_THRESHOLD}), "
        f"markers={len(markers)} (min={settings.MIN_NUTRITION_MARKERS})"
    )

    # Log all recognized text lines
    logger.info(f"[{scan_id}] OCR recognized {len(text_lines)} text lines:")
    for i, line in enumerate(text_lines, 1):
        text = line.get("text", "")
        line_conf = line.get("confidence", 0)
        logger.info(f"[{scan_id}]   Line {i}: '{text}' (conf={line_conf:.2f})")

    # Log found markers
    if markers:
        logger.info(f"[{scan_id}] Found nutrition markers: {markers}")
    else:
        logger.warning(f"[{scan_id}] NO nutrition markers found in OCR text!")

    # Log combined text for analysis
    full_text = " ".join([line.get("text", "") for line in text_lines])
    logger.info(f"[{scan_id}] Combined OCR text: '{full_text}'")
    logger.info(f"[{scan_id}] =========================================")

    # Check quality criteria
    confidence_ok = confidence >= settings.OCR_CONFIDENCE_THRESHOLD
    markers_ok = len(markers) >= settings.MIN_NUTRITION_MARKERS

    if confidence_ok and markers_ok:
        logger.info(f"[{scan_id}] Quality check PASSED → parse_ocr_nutrition")
        next_node = "parse_ocr_nutrition"
    else:
        logger.warning(
            f"[{scan_id}] Quality check FAILED → vision_fallback "
            f"(confidence={confidence_ok}, markers={markers_ok})"
        )
        next_node = "vision_fallback"

    return {
        **state,
        "next_node": next_node,
        "current_step": "check_ocr_quality",
        "progress": 50,
        "updated_at": datetime.utcnow(),
    }
