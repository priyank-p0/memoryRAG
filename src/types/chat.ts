export type ModelProvider = 'openai' | 'google' | 'anthropic';

export type ChatRole = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  role: ChatRole;
  content: string;
  timestamp: string;
  model_used?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  model_provider: ModelProvider;
  model_name: string;
  temperature: number;
  max_tokens?: number;
  system_prompt?: string;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  model_used: string;
  timestamp: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  provider: ModelProvider;
  name: string;
  display_name: string;
  description: string;
  max_tokens: number;
  supports_system_prompt: boolean;
}

export interface ChatSettings {
  model_provider: ModelProvider;
  model_name: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
}
