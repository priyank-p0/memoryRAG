"""Data models for chat functionality."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"


class ChatRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: ChatRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    message: str
    conversation_id: Optional[str] = None
    model_provider: ModelProvider
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    message: str
    conversation_id: str
    model_used: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    usage: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """Chat conversation model."""
    id: str
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ModelInfo(BaseModel):
    """Model information."""
    provider: ModelProvider
    name: str
    display_name: str
    description: str
    max_tokens: int
    supports_system_prompt: bool = True


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
