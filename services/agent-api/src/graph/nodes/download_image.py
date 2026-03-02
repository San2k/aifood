"""
Download image from URL to local /tmp directory.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


async def download_image(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download nutrition label image from photo_url or save from image_base64.

    Args:
        state: LabelProcessingState with photo_url or image_base64

    Returns:
        Updated state with local_image_path
    """
    scan_id = state["scan_id"]
    photo_url = state.get("photo_url")
    image_base64 = state.get("image_base64")

    try:
        # Create upload directory
        upload_dir = Path("/tmp/aifood/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Case 1: Base64-encoded image (from OpenClaw plugin)
        if image_base64:
            logger.info(f"[{scan_id}] Saving base64-encoded image")

            import base64

            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)

            # Auto-detect format from magic bytes
            ext = '.jpg'
            if image_bytes[:4] == b'\x89PNG':
                ext = '.png'
            elif image_bytes[:2] == b'\xff\xd8':
                ext = '.jpg'
            elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
                ext = '.webp'

            # Save to file
            local_path = upload_dir / f"{scan_id}{ext}"
            with open(local_path, 'wb') as f:
                f.write(image_bytes)

            file_size = os.path.getsize(local_path)
            logger.info(f"[{scan_id}] Saved {file_size} bytes to {local_path}")

            return {
                **state,
                "local_image_path": str(local_path),
                "current_step": "download_image",
                "progress": 10,
                "updated_at": datetime.utcnow(),
            }

        # Case 2: URL download (original behavior)
        elif photo_url:
            logger.info(f"[{scan_id}] Downloading image from {photo_url}")

            # Download image with User-Agent header
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(photo_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()

                    # Determine file extension from content-type
                    content_type = response.headers.get('Content-Type', 'image/jpeg')
                    ext = '.jpg' if 'jpeg' in content_type else '.png' if 'png' in content_type else '.jpg'

                    # Save to file
                    local_path = upload_dir / f"{scan_id}{ext}"
                    content = await response.read()

                    with open(local_path, 'wb') as f:
                        f.write(content)

            file_size = os.path.getsize(local_path)
            logger.info(f"[{scan_id}] Downloaded {file_size} bytes to {local_path}")

            return {
                **state,
                "local_image_path": str(local_path),
                "current_step": "download_image",
                "progress": 10,
                "updated_at": datetime.utcnow(),
            }

        else:
            # Neither photo_url nor image_base64 provided
            logger.error(f"[{scan_id}] No image source provided")
            return {
                **state,
                "status": "failed",
                "error_message": "No image source provided (need photo_url or image_base64)",
                "should_end": True,
            }

    except aiohttp.ClientError as e:
        logger.error(f"[{scan_id}] Download failed: {e}")
        return {
            **state,
            "status": "failed",
            "error_message": f"Failed to download image: {str(e)}",
            "should_end": True,
        }
    except Exception as e:
        logger.error(f"[{scan_id}] Unexpected error: {e}", exc_info=True)
        return {
            **state,
            "status": "failed",
            "error_message": f"Unexpected error during download: {str(e)}",
            "should_end": True,
        }
