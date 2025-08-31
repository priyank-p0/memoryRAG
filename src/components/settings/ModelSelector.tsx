import React, { useEffect } from 'react';
import { Select } from '../ui/Select';
import { Input } from '../ui/Input';
import { useChatStore } from '../../store/chatStore';
import type { ModelProvider } from '../../types/chat';

export const ModelSelector: React.FC = () => {
  const {
    availableModels,
    settings,
    updateSettings,
    loadAvailableModels,
  } = useChatStore();

  useEffect(() => {
    loadAvailableModels();
  }, [loadAvailableModels]);

  const providerOptions = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'google', label: 'Google Gemini' },
    { value: 'anthropic', label: 'Anthropic Claude' },
  ];

  const getModelsForProvider = (provider: ModelProvider) => {
    return availableModels
      .filter(model => model.provider === provider)
      .map(model => ({
        value: model.name,
        label: model.display_name,
      }));
  };

  const handleProviderChange = (provider: string) => {
    const providerModels = getModelsForProvider(provider as ModelProvider);
    const defaultModel = providerModels[0]?.value || '';
    
    updateSettings({
      model_provider: provider as ModelProvider,
      model_name: defaultModel,
    });
  };

  const currentProviderModels = getModelsForProvider(settings.model_provider);
  const selectedModel = availableModels.find(
    m => m.name === settings.model_name && m.provider === settings.model_provider
  );

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Model Configuration</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Provider Selection */}
        <Select
          label="Provider"
          value={settings.model_provider}
          onChange={(e) => handleProviderChange(e.target.value)}
          options={providerOptions}
        />

        {/* Model Selection */}
        <Select
          label="Model"
          value={settings.model_name}
          onChange={(e) => updateSettings({ model_name: e.target.value })}
          options={currentProviderModels}
        />
      </div>

      {/* Model Description */}
      {selectedModel && (
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-700">{selectedModel.description}</p>
          <p className="text-xs text-gray-500 mt-1">
            Max tokens: {selectedModel.max_tokens.toLocaleString()}
          </p>
        </div>
      )}

      {/* Temperature */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Temperature: {settings.temperature}
        </label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Focused (0.0)</span>
          <span>Balanced (1.0)</span>
          <span>Creative (2.0)</span>
        </div>
      </div>

      {/* Max Tokens */}
      <Input
        label="Max Tokens"
        type="number"
        min="1"
        max={selectedModel?.max_tokens || 4000}
        value={settings.max_tokens}
        onChange={(e) => updateSettings({ max_tokens: parseInt(e.target.value) || 1000 })}
      />

      {/* System Prompt */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          System Prompt (Optional)
        </label>
        <textarea
          value={settings.system_prompt}
          onChange={(e) => updateSettings({ system_prompt: e.target.value })}
          placeholder="Enter a system prompt to customize the AI's behavior..."
          rows={3}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
        <p className="text-xs text-gray-500 mt-1">
          The system prompt helps guide the AI's responses and behavior.
        </p>
      </div>
    </div>
  );
};
