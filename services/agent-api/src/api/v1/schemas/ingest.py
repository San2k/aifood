"""
Pydantic schemas for /v1/ingest endpoint.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class IngestRequest(BaseModel):
    """Request schema for message ingestion."""

    # User identification
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for multi-turn")

    # Input data
    input_type: Literal["text", "photo", "callback", "confirmation"] = Field("text", description="Input type")
    message: str = Field(..., description="User message text")
    message_id: int = Field(..., description="Telegram message ID")
    photo_file_id: Optional[str] = Field(None, description="Telegram photo file ID")

    # Clarification responses (if any)
    clarification_responses: Optional[Dict[str, Any]] = Field(None, description="User responses to clarifications")

    # Metadata
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "username": "john_doe",
                "first_name": "John",
                "input_type": "text",
                "message": "Съел 2 яйца и 150г гречки",
                "message_id": 12345
            }
        }


class ClarificationRequest(BaseModel):
    """Clarification request to user."""
    
    type: str = Field(..., description="Clarification type")
    question: str = Field(..., description="Question to ask user")
    options: Optional[List[str]] = Field(None, description="Answer options")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class IngestResponse(BaseModel):
    """Response schema for message ingestion."""
    
    # Status
    success: bool = Field(..., description="Whether ingestion succeeded")
    conversation_id: str = Field(..., description="Conversation ID")
    
    # Response to user
    reply_text: Optional[str] = Field(None, description="Text to send back to user")
    
    # Clarification flow
    needs_clarification: bool = Field(False, description="Whether clarification needed")
    clarification_requests: List[ClarificationRequest] = Field(default_factory=list)
    
    # Results
    saved_entries: List[int] = Field(default_factory=list, description="IDs of saved food entries")
    daily_totals: Optional[Dict[str, float]] = Field(None, description="Daily nutrition totals")
    ai_advice: Optional[str] = Field(None, description="AI-generated advice")
    
    # Errors
    errors: List[str] = Field(default_factory=list, description="Error messages if any")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "reply_text": "✅ Добавлено: 2 яйца (140 ккал), 150г гречки (195 ккал)",
                "needs_clarification": False,
                "saved_entries": [1, 2],
                "daily_totals": {
                    "calories": 1850,
                    "protein": 85,
                    "carbohydrates": 180,
                    "fat": 60
                }
            }
        }
