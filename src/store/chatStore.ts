import { create } from 'zustand';
import type { Conversation, ModelInfo, ChatSettings, ModelProvider } from '../types/chat';
import { chatApi } from '../services/api';

interface ChatState {
  // Conversations
  conversations: Conversation[];
  currentConversationId: string | null;
  currentConversation: Conversation | null;
  
  // Models
  availableModels: ModelInfo[];
  
  // Chat settings
  settings: ChatSettings;
  
  // UI state
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  sidebarOpen: boolean;
  
  // Actions
  loadConversations: () => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  createNewConversation: (title?: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
  updateConversationTitle: (conversationId: string, title: string) => Promise<void>;
  clearConversation: (conversationId: string) => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  loadAvailableModels: () => Promise<void>;
  updateSettings: (settings: Partial<ChatSettings>) => void;
  toggleSidebar: () => void;
  setError: (error: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  conversations: [],
  currentConversationId: null,
  currentConversation: null,
  availableModels: [],
  settings: {
    model_provider: 'openai' as ModelProvider,
    model_name: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 1000,
    system_prompt: '',
  },
  isLoading: false,
  isSending: false,
  error: null,
  sidebarOpen: true,

  // Actions
  loadConversations: async () => {
    try {
      set({ isLoading: true, error: null });
      const conversations = await chatApi.getConversations();
      set({ conversations, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  selectConversation: async (conversationId: string) => {
    try {
      set({ isLoading: true, error: null });
      const conversation = await chatApi.getConversation(conversationId);
      set({
        currentConversationId: conversationId,
        currentConversation: conversation,
        isLoading: false,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  createNewConversation: async (title?: string) => {
    try {
      set({ isLoading: true, error: null });
      const conversation = await chatApi.createConversation(title);
      const conversations = [...get().conversations, conversation];
      set({
        conversations,
        currentConversationId: conversation.id,
        currentConversation: conversation,
        isLoading: false,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  deleteConversation: async (conversationId: string) => {
    try {
      set({ error: null });
      await chatApi.deleteConversation(conversationId);
      const conversations = get().conversations.filter(c => c.id !== conversationId);
      const currentConversationId = get().currentConversationId;
      
      set({
        conversations,
        ...(currentConversationId === conversationId && {
          currentConversationId: null,
          currentConversation: null,
        }),
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  updateConversationTitle: async (conversationId: string, title: string) => {
    try {
      set({ error: null });
      await chatApi.updateConversationTitle(conversationId, title);
      
      const conversations = get().conversations.map(c =>
        c.id === conversationId ? { ...c, title } : c
      );
      
      const currentConversation = get().currentConversation;
      set({
        conversations,
        ...(currentConversation?.id === conversationId && {
          currentConversation: { ...currentConversation, title },
        }),
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  clearConversation: async (conversationId: string) => {
    try {
      set({ error: null });
      await chatApi.clearConversation(conversationId);
      
      const conversations = get().conversations.map(c =>
        c.id === conversationId ? { ...c, messages: [] } : c
      );
      
      const currentConversation = get().currentConversation;
      set({
        conversations,
        ...(currentConversation?.id === conversationId && {
          currentConversation: { ...currentConversation, messages: [] },
        }),
      });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  sendMessage: async (message: string) => {
    const { settings, currentConversationId, currentConversation } = get();
    
    try {
      set({ isSending: true, error: null });
      
      const response = await chatApi.sendMessage({
        message,
        conversation_id: currentConversationId || undefined,
        model_provider: settings.model_provider,
        model_name: settings.model_name,
        temperature: settings.temperature,
        max_tokens: settings.max_tokens,
        system_prompt: settings.system_prompt || undefined,
      });
      
      // Update current conversation
      const updatedConversation = await chatApi.getConversation(response.conversation_id);
      
      // Update conversations list
      const conversations = get().conversations;
      const existingIndex = conversations.findIndex(c => c.id === response.conversation_id);
      
      let updatedConversations;
      if (existingIndex >= 0) {
        updatedConversations = conversations.map((c, i) =>
          i === existingIndex ? updatedConversation : c
        );
      } else {
        updatedConversations = [...conversations, updatedConversation];
      }
      
      set({
        conversations: updatedConversations,
        currentConversationId: response.conversation_id,
        currentConversation: updatedConversation,
        isSending: false,
      });
      
    } catch (error) {
      set({ error: (error as Error).message, isSending: false });
    }
  },

  loadAvailableModels: async () => {
    try {
      set({ isLoading: true, error: null });
      const models = await chatApi.getAvailableModels();
      set({ availableModels: models, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  updateSettings: (newSettings: Partial<ChatSettings>) => {
    const currentSettings = get().settings;
    set({ settings: { ...currentSettings, ...newSettings } });
  },

  toggleSidebar: () => {
    set({ sidebarOpen: !get().sidebarOpen });
  },

  setError: (error: string | null) => {
    set({ error });
  },
}));
