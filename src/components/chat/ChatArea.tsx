import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { useChatStore } from '../../store/chatStore';

export const ChatArea: React.FC = () => {
  const {
    currentConversation,
    isSending,
    sendMessage,
  } = useChatStore();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentConversation?.messages, isSending]);

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {currentConversation ? (
          <div className="space-y-0">
            {currentConversation.messages.map((message, index) => (
              <MessageBubble
                key={index}
                message={message}
                isLast={index === currentConversation.messages.length - 1}
              />
            ))}
            {isSending && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <h3 className="text-lg font-medium mb-2">Welcome to Multi-Model Chat</h3>
              <p className="text-sm">
                Select a conversation from the sidebar or start a new one to begin chatting.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input */}
      {currentConversation && (
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isSending}
          placeholder="Type your message..."
        />
      )}
    </div>
  );
};
