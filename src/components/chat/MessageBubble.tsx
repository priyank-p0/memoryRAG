import React from 'react';
import { clsx } from 'clsx';
import { User, Bot } from 'lucide-react';
import type { ChatMessage } from '../../types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isLast?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isLast = false,
}) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  if (message.role === 'system') {
    return null; // Don't display system messages
  }
  
  return (
    <div
      className={clsx(
        'flex gap-3 p-4 animate-fade-in',
        isLast && 'animate-slide-up'
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary-600' : 'bg-gray-600'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      
      {/* Message Content */}
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">
            {isUser ? 'You' : 'Assistant'}
          </span>
          {message.model_used && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              {message.model_used}
            </span>
          )}
          <span className="text-xs text-gray-500">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        
        <div
          className={clsx(
            'prose prose-sm max-w-none',
            'text-gray-900',
            'break-words'
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    </div>
  );
};
