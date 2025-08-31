"""Abstract base class for AI model adapters."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.chat import ChatMessage, ModelInfo


class ModelAdapter(ABC):
    """Abstract base class for AI model adapters."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat completion."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models for this provider."""
        pass
    
    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Validate if model is available for this provider."""
        pass
