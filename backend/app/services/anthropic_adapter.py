"""Anthropic Claude model adapter implementation."""

import anthropic
from typing import List, Dict, Any, Optional
from ..models.chat import ChatMessage, ModelInfo, ModelProvider, ChatRole
from .model_adapter import ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Anthropic Claude API adapter."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.available_models = [
            ModelInfo(
                provider=ModelProvider.ANTHROPIC,
                name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                description="Most powerful model for complex tasks",
                max_tokens=4096
            ),
            ModelInfo(
                provider=ModelProvider.ANTHROPIC,
                name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                description="Balanced performance and speed",
                max_tokens=4096
            ),
            ModelInfo(
                provider=ModelProvider.ANTHROPIC,
                name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                description="Fastest model for simple tasks",
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
        """Generate chat completion using Anthropic Claude API."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            
            for msg in messages:
                if msg.role in [ChatRole.USER, ChatRole.ASSISTANT]:
                    anthropic_messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": anthropic_messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1000
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Make API call
            response = await self.client.messages.create(**request_params)
            
            return {
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model
            }
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available Anthropic models."""
        return self.available_models
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is available for Anthropic."""
        return any(m.name == model for m in self.available_models)
