"""
Store scan metadata in database and Redis.
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime
from ...db.repositories.scan_repository import ScanRepository
from ...services.redis_service import RedisService
from ...db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def store_scan(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store label scan metadata in database and Redis for confirmation dialog.

    Args:
        state: LabelProcessingState with all processing results

    Returns:
        Updated state with scan_db_id and status='pending_confirmation'
    """
    scan_id = state["scan_id"]
    odentity = state["odentity"]

    logger.info(f"[{scan_id}] Storing scan metadata")

    try:
        async with AsyncSessionLocal() as session:
            repo = ScanRepository(session)

            # Create scan record with basic info
            # Use "base64_upload" as placeholder if image was uploaded via base64
            scan = await repo.create_scan(
                scan_id=scan_id,
                odentity=odentity,
                photo_url=state.get("photo_url") or "base64_upload",
                status="pending_confirmation",
            )

            # Update with additional metadata
            await repo.update_scan(
                scan_id=scan_id,
                ocr_method=state.get("extraction_method"),
                ocr_confidence=state.get("confidence"),
                markers_found=state.get("markers_found", []),
                ocr_raw_text=json.dumps(state.get("ocr_raw_output", {})) if state.get("ocr_raw_output") else None,
                product_id=state.get("product_id"),
            )

            await session.commit()

            logger.info(f"[{scan_id}] Created scan DB ID={scan.id}")

        # Store in Redis for confirmation dialog (TTL 30 minutes)
        redis_service = RedisService()
        await redis_service.store_pending_scan(
            scan_id=scan_id,
            odentity=odentity,
            product_data={
                "product_id": state["product_id"],
                "product_name": state["product_name"],
                "brand": state.get("brand"),
                "nutrition_per_100g": state["nutrition_per_100g"],
                "meal_type": state.get("meal_type"),
                "consumed_at": state.get("consumed_at"),
            },
            ttl_seconds=1800,  # 30 minutes
        )

        logger.info(f"[{scan_id}] Stored in Redis for confirmation dialog")

        return {
            **state,
            "scan_db_id": scan.id,
            "status": "pending_confirmation",
            "should_end": True,
            "current_step": "store_scan",
            "progress": 100,
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"[{scan_id}] Failed to store scan: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Failed to store scan: {str(e)}",
            "should_end": True,
        }
