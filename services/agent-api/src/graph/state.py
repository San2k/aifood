"""
LangGraph State Definition.
Defines the complete state structure for nutrition bot conversation flow.
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any
from datetime import datetime


class FoodCandidate(TypedDict, total=False):
    """Food search result candidate from FatSecret."""
    food_id: str
    food_name: str
    brand_name: Optional[str]
    food_type: str  # generic, brand
    food_description: Optional[str]


class ServingOption(TypedDict, total=False):
    """Serving option with nutrition data."""
    serving_id: str
    serving_description: str
    metric_serving_amount: Optional[float]
    metric_serving_unit: Optional[str]
    measurement_description: Optional[str]
    nutrition: Dict[str, Optional[float]]  # calories, protein, carbs, fat, etc.


class ParsedFoodItem(TypedDict, total=False):
    """Parsed food item from user input."""
    name: str
    quantity: Optional[float]
    unit: Optional[str]
    cooking_method: Optional[str]
    notes: Optional[str]


class ClarificationRequest(TypedDict, total=False):
    """Request for user clarification."""
    type: Literal["weight", "cooking_method", "food_selection", "serving_selection", "confirmation", "label_confirm"]
    question: str
    options: Optional[List[str]]
    context: Dict[str, Any]


class PendingFoodEntry(TypedDict, total=False):
    """Draft food log entry being constructed."""
    food_id: Optional[str]
    food_name: str
    brand_name: Optional[str]
    serving_id: Optional[str]
    serving_description: Optional[str]
    serving_amount: Optional[float]
    serving_unit: Optional[str]
    number_of_servings: float
    nutrition: Optional[Dict[str, float]]
    meal_type: Optional[str]
    is_custom: bool


class LabelScanData(TypedDict, total=False):
    """OCR data from nutrition label."""
    product_name: Optional[str]
    brand: Optional[str]
    serving_size: Optional[Dict[str, Any]]
    nutrition_per_100g: Dict[str, Optional[float]]
    ingredients: Optional[str]
    confidence: float


class NutritionBotState(TypedDict, total=False):
    """
    Complete state for nutrition bot LangGraph.
    All fields are optional to allow partial updates.
    """
    
    # User context
    user_id: int
    telegram_id: int
    conversation_id: str
    
    # Input information
    input_type: Literal["text", "photo", "callback", "confirmation"]
    raw_input: str
    photo_file_id: Optional[str]
    message_id: int

    # Intent detection (for conversational AI)
    detected_intent: Optional[Literal["food_entry", "view_report", "question", "chat"]]
    intent_confidence: Optional[float]
    
    # Parsed data from GPT
    parsed_foods: List[ParsedFoodItem]
    ocr_text: Optional[str]
    ocr_nutrition: Optional[LabelScanData]
    
    # Food search results from FatSecret
    food_candidates: List[FoodCandidate]
    food_selection_page: int  # Current page for paginated food selection
    selected_food: Optional[FoodCandidate]
    selected_serving: Optional[ServingOption]
    
    # Entry construction
    pending_entries: List[PendingFoodEntry]
    current_entry_index: int
    
    # Clarification flow
    needs_clarification: bool
    clarification_requests: List[ClarificationRequest]
    clarification_responses: Dict[str, Any]
    
    # Results
    saved_entry_ids: List[int]
    daily_totals: Optional[Dict[str, float]]
    ai_advice: Optional[str]
    
    # Error handling
    errors: List[str]
    retry_count: int
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    # Graph routing
    next_node: Optional[str]  # For explicit routing control
    should_end: bool  # Flag to end graph execution


# Default initial state factory
def create_initial_state(
    user_id: int,
    telegram_id: int,
    conversation_id: str,
    input_type: str,
    raw_input: str,
    message_id: int,
    photo_file_id: Optional[str] = None,
    clarification_responses: Optional[Dict[str, Any]] = None
) -> NutritionBotState:
    """
    Create initial state for a new conversation turn.
    
    Args:
        user_id: Database user ID
        telegram_id: Telegram user ID
        conversation_id: Unique conversation identifier
        input_type: Type of input (text, photo, callback, confirmation)
        raw_input: Raw user input
        message_id: Telegram message ID
        photo_file_id: Telegram photo file ID (if photo input)
        clarification_responses: User responses to clarification questions
        
    Returns:
        Initial state dictionary
    """
    now = datetime.utcnow()
    
    return NutritionBotState(
        user_id=user_id,
        telegram_id=telegram_id,
        conversation_id=conversation_id,
        input_type=input_type,
        raw_input=raw_input,
        message_id=message_id,
        photo_file_id=photo_file_id,
        detected_intent=None,
        intent_confidence=None,
        parsed_foods=[],
        ocr_text=None,
        ocr_nutrition=None,
        food_candidates=[],
        selected_food=None,
        selected_serving=None,
        pending_entries=[],
        current_entry_index=0,
        needs_clarification=False,
        clarification_requests=[],
        clarification_responses=clarification_responses or {},
        saved_entry_ids=[],
        daily_totals=None,
        ai_advice=None,
        errors=[],
        retry_count=0,
        created_at=now,
        updated_at=now,
        next_node=None,
        should_end=False
    )
