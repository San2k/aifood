"""
OCR Engine using PaddleOCR for Russian nutrition label text extraction.
"""
from paddleocr import PaddleOCR
import logging
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Wrapper for PaddleOCR with Russian language support.

    Configuration:
    - lang='ru' for Russian model
    - use_angle_cls=True for auto-rotation
    - det_db_thresh=0.3 for better detection (lower threshold = more sensitive)
    - rec_thresh=0.5 for recognition confidence filtering
    """

    def __init__(self):
        """Initialize PaddleOCR with Russian language support."""
        logger.info("Initializing PaddleOCR for Russian text detection...")

        try:
            self.ocr = PaddleOCR(
                lang='ru',  # Russian language model
                use_angle_cls=True,  # Enable text angle classification (auto-rotate)
                det_db_thresh=0.3,  # Detection threshold (lower = more sensitive)
                rec_thresh=0.5,  # Recognition threshold
                use_gpu=False,  # Set to True if GPU available
                show_log=False,  # Suppress detailed PaddleOCR logs
            )
            logger.info("PaddleOCR initialized successfully with Russian model")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}", exc_info=True)
            raise

    def process(self, image_np: Any) -> List[Tuple]:
        """
        Run OCR on numpy image array.

        Args:
            image_np: numpy array of shape (H, W, C)

        Returns:
            List of (box, (text, confidence)) tuples
            Example: [
                ([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ("text", 0.95)),
                ...
            ]
        """
        try:
            logger.info(f"Running OCR on image of shape {image_np.shape}")

            # PaddleOCR returns nested list structure
            results = self.ocr.ocr(image_np, cls=True)

            # Extract first batch of results
            if results and len(results) > 0:
                batch_results = results[0]

                if batch_results:
                    logger.info(f"OCR detected {len(batch_results)} text regions")
                    return batch_results
                else:
                    logger.warning("No text detected in image")
                    return []
            else:
                logger.warning("OCR returned empty results")
                return []

        except Exception as e:
            logger.error(f"Error during OCR processing: {e}", exc_info=True)
            return []
