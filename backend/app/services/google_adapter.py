"""Google Gemini model adapter implementation."""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
from ..models.chat import ChatMessage, ModelInfo, ModelProvider, ChatRole
from .model_adapter import ModelAdapter


class GoogleAdapter(ModelAdapter):
    """Google Gemini API adapter."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.available_models = [
            ModelInfo(
                provider=ModelProvider.GOOGLE,
                name="gemini-pro",
                display_name="Gemini Pro",
                description="Google's most capable model",
                max_tokens=2048
            ),
            ModelInfo(
                provider=ModelProvider.GOOGLE,
                name="gemini-pro-vision",
                display_name="Gemini Pro Vision",
                description="Multimodal model with vision capabilities",
                max_tokens=2048
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
        """Generate chat completion using Google Gemini API."""
        try:
            # Initialize the model
            gemini_model = genai.GenerativeModel(model)
            
            # Build conversation history
            history = []
            user_message = ""
            
            for msg in messages[:-1]:  # All except the last message
                if msg.role == ChatRole.USER:
                    history.append({
                        "role": "user",
                        "parts": [msg.content]
                    })
                elif msg.role == ChatRole.ASSISTANT:
                    history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
            
            # Get the current user message
            if messages and messages[-1].role == ChatRole.USER:
                user_message = messages[-1].content
            
            # Add system prompt to the beginning if provided
            if system_prompt and history:
                history.insert(0, {
                    "role": "user",
                    "parts": [system_prompt]
                })
                history.insert(1, {
                    "role": "model",
                    "parts": ["I understand. I'll follow these instructions."]
                })
            
            # Start chat session
            chat = gemini_model.start_chat(history=history)
            
            # Generate response
            response = await chat.send_message_async(
                user_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            
            return {
                "content": response.text,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                },
                "model": model
            }
            
        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available Google models."""
        return self.available_models
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is available for Google."""
        return any(m.name == model for m in self.available_models)
