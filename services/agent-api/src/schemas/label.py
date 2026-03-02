"""
Pydantic models for nutrition label processing.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import datetime


class NutritionPer100g(BaseModel):
    """Nutrition values normalized to per 100g."""

    calories_kcal: Decimal = Field(ge=0, le=900)
    protein_g: Optional[Decimal] = Field(None, ge=0, le=100)
    carbs_g: Optional[Decimal] = Field(None, ge=0, le=100)
    fat_g: Optional[Decimal] = Field(None, ge=0, le=100)
    fiber_g: Optional[Decimal] = Field(None, ge=0, le=50)
    sugar_g: Optional[Decimal] = Field(None, ge=0, le=100)
    salt_g: Optional[Decimal] = Field(None, ge=0, le=10)
    sodium_mg: Optional[Decimal] = Field(None, ge=0, le=5000)
    kj: Optional[Decimal] = None

    @field_validator('*', mode='before')
    @classmethod
    def comma_to_dot(cls, v):
        """Convert European decimal notation (comma) to dot."""
        if isinstance(v, str):
            return Decimal(v.replace(',', '.').replace(' ', ''))
        return v

    def validate_macro_sum(self) -> None:
        """Validate that protein + carbs + fat <= 120g per 100g."""
        total = (
            (self.protein_g or Decimal(0)) +
            (self.carbs_g or Decimal(0)) +
            (self.fat_g or Decimal(0))
        )
        if total > 120:
            raise ValueError(f"Macro sum {total}g exceeds 120g per 100g")


class NutritionLabelData(BaseModel):
    """Structured nutrition label data extracted from OCR or Vision."""

    product_name: str = Field(max_length=500)
    brand: Optional[str] = Field(None, max_length=255)
    nutrition_basis: Literal['per_100g', 'per_serving']
    serving_size_g: Optional[Decimal] = None
    nutrition_per_100g: NutritionPer100g
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    extraction_method: Literal['paddleocr', 'gemini']
    markers_found: List[str] = []
    notes: Optional[str] = None


class ProcessLabelRequest(BaseModel):
    """Request to process nutrition label photo."""

    odentity: str
    photo_url: str
    meal_type: Optional[str] = None
    consumed_at: Optional[str] = None  # ISO format YYYY-MM-DD


class ProcessLabelResponse(BaseModel):
    """Response after label processing."""

    scan_id: str
    status: Literal['processing', 'pending_confirmation', 'failed']
    product: Optional[NutritionLabelData] = None
    error: Optional[str] = None


class ConfirmScanRequest(BaseModel):
    """Request to confirm and log scanned product."""

    scan_id: str
    grams_consumed: Decimal = Field(gt=0)
    edits: Optional[dict] = None  # User corrections to nutrition values
    meal_type: Optional[str] = None
    consumed_at: Optional[str] = None


class ConfirmScanResponse(BaseModel):
    """Response after confirming scan."""

    success: bool
    entry_id: Optional[int] = None
    message: str


class ScanStatusResponse(BaseModel):
    """Response for scan status polling."""

    scan_id: str
    status: Literal['processing', 'pending_confirmation', 'confirmed', 'cancelled', 'failed']
    product: Optional[NutritionLabelData] = None
    error: Optional[str] = None
    progress: int = Field(ge=0, le=100)  # 0-100
    created_at: datetime
    processed_at: Optional[datetime] = None


class ConfirmMessageRequest(BaseModel):
    """Request to handle user confirmation message."""

    odentity: str
    message_text: str


class ConfirmMessageResponse(BaseModel):
    """Response after processing confirmation message."""

    action: Literal['confirm', 'cancel', 'edit', 'unknown']
    entry_id: Optional[int] = None
    message: str
