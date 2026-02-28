"""
Conversation State model.
Stores LangGraph conversation state for multi-turn interactions.
"""

from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid

from ..base import Base


class ConversationState(Base):
    """Conversation state model for tracking LangGraph execution."""

    __tablename__ = "conversation_state"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # User Reference
    user_id = Column(BigInteger, ForeignKey("user_profile.id", ondelete="CASCADE"), nullable=False, index=True)

    # Conversation ID (unique identifier for conversation session)
    conversation_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)

    # Graph State
    current_node = Column(String(100), nullable=True)  # Current node in LangGraph
    graph_state = Column(JSONB, nullable=False, default=dict)  # Complete LangGraph state

    # Context Storage (for quick access without parsing full graph_state)
    pending_clarifications = Column(JSONB, nullable=True)  # [{type, question, options}]
    selected_food_candidates = Column(JSONB, nullable=True)  # FatSecret search results
    pending_food_entry = Column(JSONB, nullable=True)  # Draft food log entry

    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<ConversationState(id={self.id}, user_id={self.user_id}, "
            f"conversation_id={self.conversation_id}, current_node={self.current_node})>"
        )
