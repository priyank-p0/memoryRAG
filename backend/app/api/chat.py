"""Chat API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from ..models.chat import (
    ChatRequest, ChatResponse, Conversation, ModelInfo, ErrorResponse
)
from ..models.storage import ChatRecord, ChatSession
from ..services.chat_service import chat_service
from ..services.storage_service import storage_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a chat message and get AI response."""
    try:
        response = await chat_service.send_message(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    """Get all conversations."""
    try:
        conversations = chat_service.get_all_conversations()
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation."""
    try:
        conversation = chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/conversations", response_model=Conversation)
async def create_conversation(title: str = None):
    """Create a new conversation."""
    try:
        conversation = chat_service.create_conversation(title)
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        success = chat_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title."""
    try:
        success = chat_service.update_conversation_title(conversation_id, title)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}/messages")
async def clear_conversation(conversation_id: str):
    """Clear all messages from a conversation."""
    try:
        success = chat_service.clear_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """Get all available AI models."""
    try:
        models = chat_service.get_available_models()
        return models
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Storage-related endpoints
@router.get("/sessions", response_model=List[ChatSession])
async def get_all_sessions():
    """Get all chat sessions."""
    try:
        sessions = storage_service.get_all_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/records", response_model=List[ChatRecord])
async def get_session_records(session_id: str):
    """Get all chat records for a specific session."""
    try:
        records = storage_service.get_session_records(session_id)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/records", response_model=List[ChatRecord])
async def get_all_records():
    """Get all chat records."""
    try:
        records = storage_service.get_all_records()
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search", response_model=List[ChatRecord])
async def search_records(
    query: str = Query(..., description="Search query"),
    session_id: Optional[str] = Query(None, description="Optional session ID to filter by")
):
    """Search chat records by text content."""
    try:
        records = storage_service.search_records(query, session_id)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats")
async def get_storage_stats():
    """Get storage statistics."""
    try:
        stats = storage_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
