"""Pydantic schemas for API request/response models."""
from typing import Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message model for conversation history."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User prompt")
    conversation_id: Optional[str] = Field(
        None, 
        description="Optional conversation ID for context"
    )
    include_history: bool = Field(
        True, 
        description="Whether to include conversation history"
    )
    # Credentials - can be provided in request or fallback to environment variables
    openai_api_key: Optional[str] = Field(
        None, 
        description="OpenAI API key (optional if set in env)"
    )
    ido_base_url: Optional[str] = Field(
        None, 
        description="IDO system base URL (optional if set in env)"
    )
    ido_api_key: Optional[str] = Field(
        None, 
        description="IDO API key (optional if set in env)"
    )
    ido_api_secret: Optional[str] = Field(
        None, 
        description="IDO API secret (optional if set in env)"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "message": "Show me all customers",
                "conversation_id": "conv_123456",
                "include_history": True
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    reply: str = Field(..., description="Assistant's reply")
    conversation_id: Optional[str] = Field(
        None, 
        description="Conversation ID for context"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "reply": "Here are the customers...",
                "conversation_id": "conv_123456"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "status": "ok"
            }
        }


class RootResponse(BaseModel):
    """Response model for root endpoint."""
    service: str
    status: str
    endpoints: dict
    message: str
    request_format: dict
    note: str

