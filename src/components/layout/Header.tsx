import React from 'react';
import { Menu, Zap, AlertCircle, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { useChatStore } from '../../store/chatStore';
import { clsx } from 'clsx';

export const Header: React.FC = () => {
  const { toggleSidebar, error, setError, settings, currentConversation } = useChatStore();

  const getProviderIcon = () => {
    switch (settings.model_provider) {
      case 'openai':
        return '🤖';
      case 'google':
        return '🧠';
      case 'anthropic':
        return '🎭';
      default:
        return '🤖';
    }
  };

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="lg:hidden"
            >
              <Menu className="w-4 h-4" />
            </Button>
            
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-medium text-gray-900">
                {currentConversation ? currentConversation.title : 'Select a conversation'}
              </h2>
            </div>
          </div>

          {/* Current Model Info */}
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full">
            <span className="text-sm">{getProviderIcon()}</span>
            <span className="text-sm font-medium text-gray-700">
              {settings.model_name}
            </span>
            <Zap className="w-3 h-3 text-gray-500" />
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-800">{error}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="text-red-600 hover:bg-red-100"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
};
