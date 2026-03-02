"""
Image preprocessing service using OpenCV.
Improves OCR accuracy through rotation, deskew, contrast enhancement, and upscaling.
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Service for preprocessing nutrition label images before OCR."""

    def __init__(self, target_size: int = 1400):
        """
        Initialize preprocessor.

        Args:
            target_size: Target width for upscaling (1200-1600px recommended)
        """
        self.target_size = target_size

    def preprocess(self, image_path: str) -> str:
        """
        Apply full preprocessing pipeline to image.

        Pipeline:
        1. Auto-rotate (EXIF orientation)
        2. Deskew (correct angle)
        3. CLAHE (contrast enhancement if needed)
        4. Upscale (to target size if smaller)

        Args:
            image_path: Path to input image

        Returns:
            Path to preprocessed image

        Raises:
            Exception if preprocessing fails
        """
        try:
            logger.info(f"Preprocessing image: {image_path}")

            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            # 1. Auto-rotate (handle EXIF orientation)
            img = self._auto_rotate(img, image_path)

            # 2. Deskew (correct angle)
            img = self._deskew(img)

            # 3. CLAHE (contrast enhancement if needed)
            if self._is_low_contrast(img):
                logger.info("Applying CLAHE contrast enhancement")
                img = self._apply_clahe(img)

            # 4. Upscale if needed
            if img.shape[1] < self.target_size:
                logger.info(f"Upscaling image to {self.target_size}px width")
                img = self._upscale(img, self.target_size)

            # Save preprocessed image
            output_path = str(Path(image_path).with_suffix('.preprocessed.jpg'))
            cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])

            logger.info(f"Preprocessed image saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Preprocessing error: {e}", exc_info=True)
            raise

    def _auto_rotate(self, img: np.ndarray, image_path: str) -> np.ndarray:
        """
        Auto-rotate image based on EXIF orientation.

        Args:
            img: Input image (numpy array)
            image_path: Path to original image (for EXIF data)

        Returns:
            Rotated image
        """
        try:
            pil_img = Image.open(image_path)
            exif = pil_img.getexif()

            # EXIF orientation tag
            orientation_key = 274  # Orientation tag

            if exif and orientation_key in exif:
                orientation = exif[orientation_key]

                if orientation == 3:
                    img = cv2.rotate(img, cv2.ROTATE_180)
                elif orientation == 6:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                elif orientation == 8:
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                logger.debug(f"Applied EXIF rotation (orientation: {orientation})")

        except Exception as e:
            logger.warning(f"Could not read EXIF orientation: {e}")

        return img

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """
        Deskew image (correct angle).

        Uses Hough Line Transform to detect dominant lines and calculate skew angle.

        Args:
            img: Input image

        Returns:
            Deskewed image
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Hough Line Transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is not None and len(lines) > 0:
                # Calculate median angle
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta) - 90
                    angles.append(angle)

                median_angle = np.median(angles)

                # Only deskew if angle is significant (> 0.5 degrees)
                if abs(median_angle) > 0.5:
                    logger.debug(f"Deskewing by {median_angle:.2f} degrees")
                    (h, w) = img.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    img = cv2.warpAffine(
                        img, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )

        except Exception as e:
            logger.warning(f"Deskew failed: {e}")

        return img

    def _is_low_contrast(self, img: np.ndarray) -> bool:
        """
        Check if image has low contrast.

        Args:
            img: Input image

        Returns:
            True if contrast is low
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        std = np.std(gray)
        return std < 50  # Threshold for low contrast

    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Args:
            img: Input image

        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

        # Split channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge channels
        lab = cv2.merge([l, a, b])

        # Convert back to BGR
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return img

    def _upscale(self, img: np.ndarray, target_width: int) -> np.ndarray:
        """
        Upscale image to target width while maintaining aspect ratio.

        Args:
            img: Input image
            target_width: Target width in pixels

        Returns:
            Upscaled image
        """
        (h, w) = img.shape[:2]
        scale = target_width / w
        new_h = int(h * scale)

        img = cv2.resize(
            img,
            (target_width, new_h),
            interpolation=cv2.INTER_CUBIC
        )

        return img


# Global instance
image_preprocessor = ImagePreprocessor()
