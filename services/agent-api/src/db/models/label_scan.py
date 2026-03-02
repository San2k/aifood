"""
SQLAlchemy model for label_scans table.
"""
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Integer, TIMESTAMP, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from ..session import Base


class LabelScan(Base):
    """Label scan tracking for confirmation workflow."""

    __tablename__ = 'label_scans'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_id = Column(String(100), unique=True, nullable=False, index=True)
    odentity = Column(String(255), nullable=False, index=True)

    # Input
    photo_url = Column(Text, nullable=False)
    photo_local_path = Column(Text)

    # Processing metadata
    status = Column(String(50), nullable=False, default='processing', index=True)
    ocr_method = Column(String(50))  # 'paddleocr' or 'gemini'
    ocr_confidence = Column(Numeric(5, 4))
    markers_found = Column(ARRAY(Text))

    # Raw OCR data (for debugging)
    ocr_raw_text = Column(Text)
    ocr_structured_data = Column(JSONB)

    # Extracted product data
    product_id = Column(BigInteger, ForeignKey('custom_products.id'))

    # User edits
    user_edits = Column(JSONB)

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(TIMESTAMP(timezone=True))
    confirmed_at = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'pending_confirmation', 'confirmed', 'cancelled', 'failed')",
            name='check_status_values'
        ),
        CheckConstraint(
            'ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 1)',
            name='check_ocr_confidence'
        ),
    )

    def __repr__(self):
        return f"<LabelScan(scan_id='{self.scan_id}', status='{self.status}', odentity='{self.odentity}')>"
