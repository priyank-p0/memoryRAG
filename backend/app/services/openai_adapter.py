"""OpenAI model adapter implementation."""

import openai
from typing import List, Dict, Any, Optional
from ..models.chat import ChatMessage, ModelInfo, ModelProvider, ChatRole
from .model_adapter import ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """OpenAI API adapter."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.available_models = [
            ModelInfo(
                provider=ModelProvider.OPENAI,
                name="gpt-4-turbo-preview",
                display_name="GPT-4 Turbo",
                description="Latest GPT-4 model with improved performance",
                max_tokens=4096
            ),
            ModelInfo(
                provider=ModelProvider.OPENAI,
                name="gpt-4",
                display_name="GPT-4",
                description="High-quality reasoning model",
                max_tokens=8192
            ),
            ModelInfo(
                provider=ModelProvider.OPENAI,
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                description="Fast and efficient model",
                max_tokens=4096
            )
        ]
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                openai_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add conversation messages
            for msg in messages:
                openai_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available OpenAI models."""
        return self.available_models
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is available for OpenAI."""
        return any(m.name == model for m in self.available_models)
