"""
Label processing API endpoints.
"""
import logging
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from ....graph.graph import process_label
from ....services.redis_service import RedisService
from ....db.repositories.scan_repository import ScanRepository
from ....db.repositories.food_log_repository import FoodLogRepository
from ....db.session import AsyncSessionLocal
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["label"])


# Request/Response models
class ProcessLabelRequest(BaseModel):
    """Request to process nutrition label photo."""
    odentity: str = Field(..., description="User identifier")
    photo_url: Optional[str] = Field(None, description="URL of nutrition label photo")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    meal_type: Optional[str] = Field(None, description="breakfast, lunch, dinner, snack")
    consumed_at: Optional[str] = Field(None, description="ISO datetime string")

    @model_validator(mode='after')
    def validate_image_source(self):
        """Ensure either photo_url or image_base64 is provided."""
        if not self.photo_url and not self.image_base64:
            raise ValueError("Either photo_url or image_base64 must be provided")
        if self.photo_url and self.image_base64:
            raise ValueError("Provide only one: photo_url or image_base64")
        return self


class ProcessLabelResponse(BaseModel):
    """Response with processing results."""
    scan_id: str
    status: str
    product: Optional[dict] = None
    error: Optional[str] = None
    progress: int = 0


class ConfirmMessageRequest(BaseModel):
    """User confirmation message."""
    odentity: str
    message_text: str


class ConfirmMessageResponse(BaseModel):
    """Confirmation action result."""
    action: str  # confirm, cancel, edit, unknown
    entry_id: Optional[int] = None
    message: str


class ScanStatusResponse(BaseModel):
    """Scan status."""
    scan_id: str
    status: str
    progress: int
    product: Optional[dict] = None
    error: Optional[str] = None


@router.post("/process_label", response_model=ProcessLabelResponse)
async def process_label_endpoint(request: ProcessLabelRequest) -> ProcessLabelResponse:
    """
    Process nutrition label photo.

    Flow:
    1. Generate unique scan_id
    2. Run LangGraph workflow
    3. Return status and product data
    """
    scan_id = str(uuid4())
    logger.info(f"[{scan_id}] Processing label for {request.odentity}")

    try:
        # Run workflow (validation already done by Pydantic)
        final_state = await process_label(
            scan_id=scan_id,
            odentity=request.odentity,
            photo_url=request.photo_url,
            image_base64=request.image_base64,
            meal_type=request.meal_type,
            consumed_at=request.consumed_at,
        )

        status = final_state.get("status", "failed")
        error = final_state.get("error_message")

        # Build product data
        product = None
        if status == "pending_confirmation" and final_state.get("product_id"):
            nutrition = final_state.get("nutrition_per_100g", {})
            product = {
                "product_id": final_state.get("product_id"),
                "product_name": final_state.get("product_name"),
                "brand": final_state.get("brand"),
                "nutrition_per_100g": {
                    "calories_kcal": float(nutrition.get("calories_kcal", 0)),
                    "protein_g": float(nutrition.get("protein_g", 0)),
                    "carbs_g": float(nutrition.get("carbs_g", 0)),
                    "fat_g": float(nutrition.get("fat_g", 0)),
                    "fiber_g": float(nutrition.get("fiber_g", 0)) if nutrition.get("fiber_g") else None,
                    "sugar_g": float(nutrition.get("sugar_g", 0)) if nutrition.get("sugar_g") else None,
                },
                "extraction_method": final_state.get("extraction_method"),
                "confidence": final_state.get("confidence"),
            }

        return ProcessLabelResponse(
            scan_id=scan_id,
            status=status,
            product=product,
            error=error,
            progress=final_state.get("progress", 0),
        )

    except Exception as e:
        logger.error(f"[{scan_id}] Endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scan_status/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """
    Get scan processing status.

    Used for polling during async processing.
    """
    try:
        # Check Redis first (for pending scans)
        redis_service = RedisService()
        pending_data = await redis_service.get_pending_scan(scan_id)

        if pending_data:
            return ScanStatusResponse(
                scan_id=scan_id,
                status="pending_confirmation",
                progress=100,
                product=pending_data,
            )

        # Check database
        async with AsyncSessionLocal() as session:
            repo = ScanRepository(session)
            scan = await repo.get_scan_by_id(scan_id)

            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")

            product = None
            if scan.product_id:
                # Fetch product data
                from ....db.repositories.product_repository import ProductRepository
                prod_repo = ProductRepository(session)
                prod = await prod_repo.get_custom_product(scan.product_id)

                if prod:
                    product = {
                        "product_id": prod.id,
                        "product_name": prod.product_name,
                        "brand": prod.brand_name,
                        "nutrition_per_100g": {
                            "calories_kcal": float(prod.calories_per_100g),
                            "protein_g": float(prod.protein_per_100g or 0),
                            "carbs_g": float(prod.carbs_per_100g or 0),
                            "fat_g": float(prod.fat_per_100g or 0),
                        }
                    }

            return ScanStatusResponse(
                scan_id=scan_id,
                status=scan.status,
                progress=100 if scan.status in ["confirmed", "cancelled", "failed"] else 90,
                product=product,
                error=scan.error_message,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/confirm_message", response_model=ConfirmMessageResponse)
async def confirm_message_endpoint(request: ConfirmMessageRequest) -> ConfirmMessageResponse:
    """
    Process user confirmation message.

    Actions:
    - "подтвердить 150г" → log to food_log_entry
    - "отменить" → mark scan cancelled
    - "исправить калории 300" → update nutrition values
    """
    message = request.message_text.lower().strip()
    odentity = request.odentity

    logger.info(f"Confirmation message from {odentity}: {message}")

    try:
        # Check if user has pending scan
        redis_service = RedisService()
        pending_scan = await redis_service.get_pending_scan_for_user(odentity)

        if not pending_scan:
            return ConfirmMessageResponse(
                action="unknown",
                message="No pending scan found. This is a normal message.",
            )

        scan_id = pending_scan["scan_id"]
        product_data = pending_scan["product_data"]

        # Detect action
        if "подтвердить" in message or "confirm" in message:
            # Extract grams (default 100g)
            import re
            grams_match = re.search(r'(\d+)\s*г', message)
            grams = float(grams_match.group(1)) if grams_match else 100.0

            # Calculate nutrition for portion
            nutrition = product_data["nutrition_per_100g"]
            multiplier = grams / 100.0

            # Log to food_log_entry
            async with AsyncSessionLocal() as session:
                food_log_repo = FoodLogRepository(session)

                entry = await food_log_repo.create_entry(
                    odentity=odentity,
                    custom_product_id=product_data["product_id"],
                    food_name=product_data["product_name"],
                    calories=Decimal(str(nutrition["calories_kcal"] * multiplier)),
                    protein=Decimal(str(nutrition.get("protein_g", 0) * multiplier)),
                    carbohydrates=Decimal(str(nutrition.get("carbs_g", 0) * multiplier)),
                    fat=Decimal(str(nutrition.get("fat_g", 0) * multiplier)),
                    meal_type=product_data.get("meal_type"),
                    consumed_at=datetime.fromisoformat(product_data["consumed_at"]) if product_data.get("consumed_at") else datetime.utcnow(),
                )

                # Update scan status
                scan_repo = ScanRepository(session)
                await scan_repo.update_scan_status(scan_id, "confirmed")

                await session.commit()

            # Clear from Redis
            await redis_service.clear_pending_scan(odentity)

            logger.info(f"[{scan_id}] Confirmed: logged {grams}g as entry {entry.id}")

            return ConfirmMessageResponse(
                action="confirm",
                entry_id=entry.id,
                message=f"✅ Записано: {product_data['product_name']} ({grams}г)",
            )

        elif "отменить" in message or "cancel" in message:
            # Cancel scan
            async with AsyncSessionLocal() as session:
                scan_repo = ScanRepository(session)
                await scan_repo.update_scan_status(scan_id, "cancelled")
                await session.commit()

            await redis_service.clear_pending_scan(odentity)

            logger.info(f"[{scan_id}] Cancelled by user")

            return ConfirmMessageResponse(
                action="cancel",
                message="❌ Сканирование отменено",
            )

        elif "исправить" in message or "edit" in message:
            # TODO: Implement edit functionality
            return ConfirmMessageResponse(
                action="edit",
                message="🔧 Редактирование пока не реализовано. Используйте 'отменить' и повторите сканирование.",
            )

        else:
            return ConfirmMessageResponse(
                action="unknown",
                message="Не понял команду. Используйте 'подтвердить 150г' или 'отменить'.",
            )

    except Exception as e:
        logger.error(f"Confirmation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
