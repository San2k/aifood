"""
Weight History Model.
Tracks user weight changes over time.
"""

from sqlalchemy import Column, BigInteger, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import Base


class WeightHistory(Base):
    """Weight history tracking model."""

    __tablename__ = "weight_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False, index=True)
    weight_kg = Column(Numeric(5, 2), nullable=False)  # Weight in kg
    measured_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    notes = Column(Text, nullable=True)  # Optional notes from user
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user = relationship("UserProfile", back_populates="weight_history")

    def __repr__(self):
        return f"<WeightHistory(id={self.id}, user_id={self.user_id}, weight={self.weight_kg}kg, date={self.measured_at})>"
