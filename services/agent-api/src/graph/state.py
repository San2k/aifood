"""
LangGraph state definition for label processing workflow.
"""
from typing import TypedDict, Optional, List, Dict, Any, Literal
from datetime import datetime


class LabelProcessingState(TypedDict, total=False):
    """
    State for nutrition label processing workflow.

    This state is passed between all LangGraph nodes.
    total=False allows optional fields.
    """

    # ========== Input ==========
    scan_id: str  # UUID for tracking
    odentity: str  # User identifier
    photo_url: Optional[str]  # URL of nutrition label photo (or None if image_base64 provided)
    image_base64: Optional[str]  # Base64-encoded image (or None if photo_url provided)
    meal_type: Optional[str]  # breakfast, lunch, dinner, snack
    consumed_at: Optional[str]  # ISO datetime string

    # ========== Image Processing ==========
    local_image_path: str  # Downloaded image path in /tmp
    preprocessed_image_path: str  # Preprocessed image path

    # ========== OCR Results ==========
    ocr_raw_output: Dict[str, Any]  # Full OCR service response
    ocr_text_lines: List[Dict[str, Any]]  # [{text, confidence, box}]
    ocr_global_confidence: float  # 0.0-1.0
    markers_found: List[str]  # ['ккал', 'белк', '100 г', ...]

    # ========== Parsed Nutrition ==========
    product_name: str
    brand: Optional[str]
    nutrition_basis: Literal['per_100g', 'per_serving']
    serving_size_g: Optional[float]
    nutrition_per_100g: Dict[str, Optional[float]]  # Always normalized to per 100g
    ingredients: Optional[str]
    allergens: Optional[str]

    # ========== Metadata ==========
    extraction_method: Literal['paddleocr', 'gemini']  # Which method was used
    confidence: float  # Overall confidence (0.0-1.0)
    notes: Optional[str]  # Warnings or observations

    # ========== Database IDs ==========
    product_id: Optional[int]  # Created custom_product.id
    scan_db_id: Optional[int]  # label_scan.id

    # ========== Status & Control ==========
    status: Literal['processing', 'pending_confirmation', 'confirmed', 'failed']
    error_message: Optional[str]
    next_node: Optional[str]  # Routing hint for conditional edges
    should_end: bool  # Whether to end workflow

    # ========== Timestamps ==========
    created_at: datetime
    updated_at: datetime

    # ========== Progress Tracking ==========
    current_step: str  # Current processing step name
    progress: int  # 0-100
