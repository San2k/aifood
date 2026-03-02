"""
HTTP client for OCR service.
"""
import aiohttp
import logging
from typing import Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)


class OCRClient:
    """Client for calling OCR service API."""

    def __init__(self):
        self.base_url = settings.OCR_SERVICE_URL
        self.timeout = settings.OCR_TIMEOUT

    async def process_image(self, image_base64: str) -> Dict[str, Any]:
        """
        Send image to OCR service for text extraction.

        Args:
            image_base64: Base64-encoded image data

        Returns:
            OCR response with:
            - text_lines: [{text, confidence, box}]
            - global_confidence: float (0.0-1.0)
            - markers_found: list of nutrition markers
            - error: error message if failed

        Raises:
            Exception if OCR service call fails
        """
        url = f"{self.base_url}/ocr"

        try:
            logger.info(f"Calling OCR service at {url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"image_base64": image_base64},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"OCR completed: {len(data.get('text_lines', []))} lines, "
                            f"confidence: {data.get('global_confidence', 0):.3f}"
                        )
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"OCR service error: {response.status} - {error_text}")
                        return {"error": f"OCR service returned {response.status}: {error_text}"}

        except aiohttp.ClientError as e:
            logger.error(f"OCR service connection error: {e}", exc_info=True)
            return {"error": f"Failed to connect to OCR service: {str(e)}"}
        except Exception as e:
            logger.error(f"OCR client error: {e}", exc_info=True)
            return {"error": f"OCR processing failed: {str(e)}"}


# Global instance
ocr_client = OCRClient()
