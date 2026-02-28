"""
Repository for conversation state management.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.conversation_state import ConversationState

logger = logging.getLogger(__name__)


def serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize state for JSON storage - convert datetime objects to ISO strings.

    Args:
        state: State dictionary

    Returns:
        Serialized state dictionary
    """
    serialized = {}
    for key, value in state.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_state(value)
        elif isinstance(value, list):
            serialized[key] = [
                serialize_state(item) if isinstance(item, dict) else
                item.isoformat() if isinstance(item, datetime) else
                item
                for item in value
            ]
        else:
            serialized[key] = value
    return serialized


def deserialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize state from JSON storage - convert ISO strings back to datetime.

    Args:
        state: Serialized state dictionary

    Returns:
        Deserialized state dictionary
    """
    deserialized = {}
    for key, value in state.items():
        if key in ['created_at', 'updated_at', 'expires_at'] and isinstance(value, str):
            try:
                deserialized[key] = datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                deserialized[key] = value
        elif isinstance(value, dict):
            deserialized[key] = deserialize_state(value)
        elif isinstance(value, list):
            deserialized[key] = [
                deserialize_state(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            deserialized[key] = value
    return deserialized


class ConversationRepository:
    """Repository for conversation state operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation state by conversation ID.

        Args:
            conversation_id: Conversation UUID

        Returns:
            State dictionary or None
        """
        stmt = select(ConversationState).where(
            ConversationState.conversation_id == conversation_id,
            ConversationState.is_active == True
        )
        result = await self.session.execute(stmt)
        conv_state = result.scalar_one_or_none()

        if conv_state:
            logger.info(f"Found conversation state: {conversation_id}")
            return deserialize_state(conv_state.graph_state)

        logger.info(f"No active conversation state found: {conversation_id}")
        return None

    async def save_conversation_state(
        self,
        user_id: int,
        conversation_id: str,
        current_node: str,
        graph_state: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ) -> ConversationState:
        """
        Save or update conversation state.

        Args:
            user_id: Database user ID
            conversation_id: Conversation UUID
            current_node: Current graph node
            graph_state: Complete graph state dictionary
            expires_at: Expiration timestamp

        Returns:
            Created or updated ConversationState
        """
        # Serialize state for JSON storage
        serialized_state = serialize_state(graph_state)

        # Check if conversation exists
        stmt = select(ConversationState).where(
            ConversationState.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        conv_state = result.scalar_one_or_none()

        if conv_state:
            # Update existing
            conv_state.current_node = current_node
            conv_state.graph_state = serialized_state
            conv_state.is_active = True  # Reactivate when saving (e.g., after clarification)
            conv_state.updated_at = datetime.utcnow()
            if expires_at:
                conv_state.expires_at = expires_at
            logger.info(f"Updated conversation state: {conversation_id}")
        else:
            # Create new
            conv_state = ConversationState(
                user_id=user_id,
                conversation_id=conversation_id,
                current_node=current_node,
                graph_state=serialized_state,
                is_active=True,
                expires_at=expires_at
            )
            self.session.add(conv_state)
            logger.info(f"Created new conversation state: {conversation_id}")

        await self.session.commit()
        await self.session.refresh(conv_state)
        return conv_state

    async def deactivate_conversation(self, conversation_id: str) -> None:
        """
        Mark conversation as inactive (completed or failed).

        Args:
            conversation_id: Conversation UUID
        """
        stmt = select(ConversationState).where(
            ConversationState.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        conv_state = result.scalar_one_or_none()

        if conv_state:
            conv_state.is_active = False
            conv_state.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.info(f"Deactivated conversation: {conversation_id}")
