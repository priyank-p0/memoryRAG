"""Chat service for managing conversations and AI model interactions."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from ..models.chat import (
    ChatMessage, ChatRequest, ChatResponse, Conversation, 
    ModelProvider, ChatRole, ModelInfo
)
from ..config import settings
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .anthropic_adapter import AnthropicAdapter


class ChatService:
    """Service for managing chat conversations and AI model interactions."""
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.model_adapters = {
            ModelProvider.OPENAI: OpenAIAdapter(settings.openai_api_key),
            ModelProvider.GOOGLE: GoogleAdapter(settings.google_api_key),
            ModelProvider.ANTHROPIC: AnthropicAdapter(settings.anthropic_api_key)
        }
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get all available models from all providers."""
        models = []
        for adapter in self.model_adapters.values():
            models.extend(adapter.get_available_models())
        return models
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def get_all_conversations(self) -> List[Conversation]:
        """Get all conversations."""
        return list(self.conversations.values())
    
    def create_conversation(self, title: str = None) -> Conversation:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.conversations[conversation_id] = conversation
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """Send a message and get AI response."""
        try:
            # Get or create conversation
            if request.conversation_id and request.conversation_id in self.conversations:
                conversation = self.conversations[request.conversation_id]
            else:
                conversation = self.create_conversation()
            
            # Add user message to conversation
            user_message = ChatMessage(
                role=ChatRole.USER,
                content=request.message,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(user_message)
            
            # Get appropriate model adapter
            adapter = self.model_adapters.get(request.model_provider)
            if not adapter:
                raise ValueError(f"Unsupported model provider: {request.model_provider}")
            
            # Validate model
            if not adapter.validate_model(request.model_name):
                raise ValueError(f"Invalid model: {request.model_name}")
            
            # Generate AI response
            ai_response = await adapter.chat_completion(
                messages=conversation.messages,
                model=request.model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt=request.system_prompt
            )
            
            # Add AI message to conversation
            ai_message = ChatMessage(
                role=ChatRole.ASSISTANT,
                content=ai_response["content"],
                timestamp=datetime.utcnow(),
                model_used=ai_response["model"]
            )
            conversation.messages.append(ai_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            # Return response
            return ChatResponse(
                message=ai_response["content"],
                conversation_id=conversation.id,
                model_used=ai_response["model"],
                timestamp=datetime.utcnow(),
                usage=ai_response.get("usage")
            )
            
        except Exception as e:
            raise Exception(f"Error in chat service: {str(e)}")
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].title = title
            self.conversations[conversation_id].updated_at = datetime.utcnow()
            return True
        return False
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages from a conversation."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages = []
            self.conversations[conversation_id].updated_at = datetime.utcnow()
            return True
        return False


# Global chat service instance
chat_service = ChatService()
