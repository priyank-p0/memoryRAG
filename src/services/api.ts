import axios from 'axios';
import type { ChatRequest, ChatResponse, Conversation, ModelInfo } from '../types/chat';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  // Send a chat message
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/send', request);
    return response.data;
  },

  // Get all conversations
  getConversations: async (): Promise<Conversation[]> => {
    const response = await api.get('/api/chat/conversations');
    return response.data;
  },

  // Get a specific conversation
  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get(`/api/chat/conversations/${conversationId}`);
    return response.data;
  },

  // Create a new conversation
  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await api.post('/api/chat/conversations', null, {
      params: { title },
    });
    return response.data;
  },

  // Delete a conversation
  deleteConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/api/chat/conversations/${conversationId}`);
  },

  // Update conversation title
  updateConversationTitle: async (conversationId: string, title: string): Promise<void> => {
    await api.put(`/api/chat/conversations/${conversationId}/title`, null, {
      params: { title },
    });
  },

  // Clear conversation messages
  clearConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/api/chat/conversations/${conversationId}/messages`);
  },

  // Get available models
  getAvailableModels: async (): Promise<ModelInfo[]> => {
    const response = await api.get('/api/chat/models');
    return response.data;
  },
};

export default api;
