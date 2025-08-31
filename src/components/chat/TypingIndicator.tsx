import React from 'react';
import { Bot } from 'lucide-react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3 p-4 animate-fade-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
        <Bot className="w-4 h-4 text-white" />
      </div>
      
      {/* Typing indicator */}
      <div className="flex-1 space-y-1">
        <div className="text-sm font-medium text-gray-900">Assistant</div>
        <div className="flex items-center gap-1">
          <span className="text-sm text-gray-500">Typing</span>
          <div className="typing-indicator">
            <div></div>
            <div></div>
            <div></div>
          </div>
        </div>
      </div>
    </div>
  );
};
