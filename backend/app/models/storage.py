"""Data models for JSON storage."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ChatEntry(BaseModel):
    """Individual chat entry with user input and response."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    text: str
    chat_session: str


class ChatRecord(BaseModel):
    """Complete chat record with user input and model response."""
    user_input: ChatEntry
    response: ChatEntry
    
    @classmethod
    def create(cls, user_text: str, response_text: str, chat_session_id: str) -> "ChatRecord":
        """Create a new chat record."""
        timestamp = datetime.utcnow()
        
        return cls(
            user_input=ChatEntry(
                timestamp=timestamp,
                text=user_text,
                chat_session=chat_session_id
            ),
            response=ChatEntry(
                timestamp=timestamp,
                text=response_text,
                chat_session=chat_session_id
            )
        )


class ChatSession(BaseModel):
    """Chat session metadata."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    title: Optional[str] = None
    
    @classmethod
    def create_new(cls, title: Optional[str] = None) -> "ChatSession":
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        return cls(
            session_id=session_id,
            title=title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
