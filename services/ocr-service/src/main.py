"""
OCR Service - FastAPI application for nutrition label text extraction.
Uses PaddleOCR with Russian language support.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import base64
import io
from PIL import Image
import numpy as np

from .ocr_engine import OCREngine
from .marker_detector import MarkerDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OCR Service",
    description="Nutrition label OCR service using PaddleOCR (Russian)",
    version="1.0.0"
)

# Initialize OCR engine and marker detector (global instances)
ocr_engine = OCREngine()
marker_detector = MarkerDetector()


class OCRRequest(BaseModel):
    """Request model for OCR processing."""
    image_base64: str


class TextLine(BaseModel):
    """Model for a single OCR text line."""
    text: str
    confidence: float
    box: List[List[float]]


class OCRResponse(BaseModel):
    """Response model for OCR processing."""
    text_lines: List[Dict[str, Any]]
    global_confidence: float
    markers_found: List[str]
    error: str | None = None


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        Service status
    """
    return {
        "status": "ok",
        "service": "ocr-service",
        "version": "1.0.0"
    }


@app.post("/ocr", response_model=OCRResponse)
async def process_ocr(request: OCRRequest):
    """
    Process image with PaddleOCR.

    Args:
        request: OCRRequest with base64-encoded image

    Returns:
        OCRResponse with:
        - text_lines: [{text, confidence, box}]
        - global_confidence: average confidence across all lines
        - markers_found: ['ккал', 'белк', '100 г', ...]
        - error: error message if processing failed

    Example:
        ```
        POST /ocr
        {
          "image_base64": "base64_encoded_image_data..."
        }

        Response:
        {
          "text_lines": [
            {"text": "Энергетическая ценность", "confidence": 0.95, "box": [[...]]},
            {"text": "250 ккал", "confidence": 0.98, "box": [[...]]}
          ],
          "global_confidence": 0.87,
          "markers_found": ["ккал", "белк", "100 г"]
        }
        ```
    """
    try:
        logger.info("Received OCR request")

        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_base64)
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert PIL Image to numpy array
            image_np = np.array(image)
            logger.info(f"Image decoded successfully: {image_np.shape}")

        except Exception as e:
            logger.error(f"Failed to decode image: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image data: {str(e)}"
            )

        # Run PaddleOCR
        ocr_results = ocr_engine.process(image_np)

        if not ocr_results:
            logger.warning("No text detected in image")
            return OCRResponse(
                text_lines=[],
                global_confidence=0.0,
                markers_found=[],
                error="No text detected in image"
            )

        # Extract text lines with confidence
        text_lines = []
        confidences = []

        for result in ocr_results:
            box, (text, confidence) = result

            # Convert numpy arrays to lists for JSON serialization
            if hasattr(box, 'tolist'):
                box = box.tolist()

            text_lines.append({
                "text": text,
                "confidence": float(confidence),
                "box": box
            })
            confidences.append(float(confidence))

        # Calculate global confidence (weighted average)
        global_conf = sum(confidences) / len(confidences) if confidences else 0.0

        # Concatenate all text for marker detection
        all_text = " ".join([line["text"] for line in text_lines])

        # Detect nutrition markers
        markers = marker_detector.find_markers(all_text)

        logger.info(
            f"OCR completed: {len(text_lines)} lines, "
            f"confidence: {global_conf:.3f}, "
            f"markers: {len(markers)}"
        )

        return OCRResponse(
            text_lines=text_lines,
            global_confidence=float(global_conf),
            markers_found=markers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
