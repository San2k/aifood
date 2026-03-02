"""
LangGraph workflow for label processing.
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import LabelProcessingState
from .nodes.download_image import download_image
from .nodes.preprocess_image import preprocess_image
from .nodes.ocr_extract import ocr_extract
from .nodes.check_ocr_quality import check_ocr_quality
from .nodes.parse_ocr_nutrition import parse_ocr_nutrition
from .nodes.vision_fallback import vision_fallback
from .nodes.validate_nutrition import validate_nutrition
from .nodes.create_product import create_product
from .nodes.store_scan import store_scan

logger = logging.getLogger(__name__)


def should_end(state: Dict[str, Any]) -> bool:
    """Check if workflow should end."""
    return state.get("should_end", False)


def route_after_quality_check(state: Dict[str, Any]) -> str:
    """
    Route after OCR quality check.

    Returns:
        - END if previous step failed (should_end=True)
        - "parse_ocr_nutrition" if quality is good
        - "vision_fallback" if quality is poor
    """
    if state.get("should_end"):
        return END
    return state.get("next_node", "parse_ocr_nutrition")


def route_after_parse(state: Dict[str, Any]) -> str:
    """
    Route after OCR parsing attempt.

    Returns:
        - END if previous step failed (should_end=True)
        - "validate_nutrition" if parsing succeeded
        - "vision_fallback" if parsing failed
    """
    if state.get("should_end"):
        return END
    next_node = state.get("next_node")
    if next_node == "vision_fallback":
        return "vision_fallback"
    return "validate_nutrition"


def build_label_processing_graph() -> StateGraph:
    """
    Build the LangGraph workflow for label processing.

    Flow:
    START
      → download_image
      → preprocess_image
      → ocr_extract
      → check_ocr_quality
        ├─ (good) → parse_ocr_nutrition
        │            ├─ (success) → validate_nutrition
        │            └─ (failed) → vision_fallback → validate_nutrition
        └─ (poor) → vision_fallback → validate_nutrition
      → validate_nutrition
      → create_product
      → store_scan
    END
    """
    workflow = StateGraph(LabelProcessingState)

    # Add nodes
    workflow.add_node("download_image", download_image)
    workflow.add_node("preprocess_image", preprocess_image)
    workflow.add_node("ocr_extract", ocr_extract)
    workflow.add_node("check_ocr_quality", check_ocr_quality)
    workflow.add_node("parse_ocr_nutrition", parse_ocr_nutrition)
    workflow.add_node("vision_fallback", vision_fallback)
    workflow.add_node("validate_nutrition", validate_nutrition)
    workflow.add_node("create_product", create_product)
    workflow.add_node("store_scan", store_scan)

    # Set entry point
    workflow.set_entry_point("download_image")

    # Add edges with should_end checks
    workflow.add_conditional_edges(
        "download_image",
        lambda state: END if state.get("should_end") else "preprocess_image",
        {
            "preprocess_image": "preprocess_image",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "preprocess_image",
        lambda state: END if state.get("should_end") else "ocr_extract",
        {
            "ocr_extract": "ocr_extract",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "ocr_extract",
        lambda state: END if state.get("should_end") else "check_ocr_quality",
        {
            "check_ocr_quality": "check_ocr_quality",
            END: END,
        }
    )

    # Conditional routing after quality check
    workflow.add_conditional_edges(
        "check_ocr_quality",
        route_after_quality_check,
        {
            "parse_ocr_nutrition": "parse_ocr_nutrition",
            "vision_fallback": "vision_fallback",
            END: END,
        }
    )

    # Conditional routing after OCR parsing (may fallback to vision)
    workflow.add_conditional_edges(
        "parse_ocr_nutrition",
        route_after_parse,
        {
            "validate_nutrition": "validate_nutrition",
            "vision_fallback": "vision_fallback",
            END: END,
        }
    )

    # Vision fallback goes to validation (or END if failed)
    workflow.add_conditional_edges(
        "vision_fallback",
        lambda state: END if state.get("should_end") else "validate_nutrition",
        {
            "validate_nutrition": "validate_nutrition",
            END: END,
        }
    )

    # Validation goes to create product (or END if failed)
    workflow.add_conditional_edges(
        "validate_nutrition",
        lambda state: END if state.get("should_end") else "create_product",
        {
            "create_product": "create_product",
            END: END,
        }
    )

    # Create product goes to store scan (or END if failed)
    workflow.add_conditional_edges(
        "create_product",
        lambda state: END if state.get("should_end") else "store_scan",
        {
            "store_scan": "store_scan",
            END: END,
        }
    )

    # Final edge to END
    workflow.add_edge("store_scan", END)

    return workflow.compile()


# Create singleton instance
label_processing_graph = build_label_processing_graph()


async def process_label(
    scan_id: str,
    odentity: str,
    photo_url: str | None = None,
    image_base64: str | None = None,
    meal_type: str | None = None,
    consumed_at: str | None = None,
) -> Dict[str, Any]:
    """
    Process nutrition label through the complete workflow.

    Args:
        scan_id: Unique scan identifier
        odentity: User identifier
        photo_url: URL of label photo (optional if image_base64 provided)
        image_base64: Base64-encoded image data (optional if photo_url provided)
        meal_type: Optional meal type (breakfast, lunch, dinner, snack)
        consumed_at: Optional ISO datetime string

    Returns:
        Final state with processing results
    """
    from datetime import datetime

    initial_state: LabelProcessingState = {
        "scan_id": scan_id,
        "odentity": odentity,
        "photo_url": photo_url,
        "image_base64": image_base64,
        "meal_type": meal_type,
        "consumed_at": consumed_at,
        "status": "processing",
        "should_end": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "progress": 0,
        "current_step": "start",
    }

    logger.info(f"[{scan_id}] Starting label processing workflow")

    try:
        # Run the graph
        final_state = await label_processing_graph.ainvoke(initial_state)

        logger.info(
            f"[{scan_id}] Workflow complete: "
            f"status={final_state.get('status')}, "
            f"product_id={final_state.get('product_id')}"
        )

        return final_state

    except Exception as e:
        logger.error(f"[{scan_id}] Workflow error: {e}", exc_info=True)
        return {
            **initial_state,
            "status": "failed",
            "error_message": f"Workflow error: {str(e)}",
            "should_end": True,
        }
