import React, { useEffect, useState } from 'react';
import { Plus, MessageSquare, Trash2, Edit2, X, Check } from 'lucide-react';
import { Button } from '../ui/Button';
import { useChatStore } from '../../store/chatStore';
import { clsx } from 'clsx';

export const ConversationList: React.FC = () => {
  const {
    conversations,
    currentConversationId,
    loadConversations,
    selectConversation,
    createNewConversation,
    deleteConversation,
    updateConversationTitle,
  } = useChatStore();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleCreateNew = () => {
    createNewConversation();
  };

  const handleEdit = (conversation: any) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleSaveEdit = () => {
    if (editingId && editTitle.trim()) {
      updateConversationTitle(editingId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleDelete = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      deleteConversation(conversationId);
    }
  };

  const sortedConversations = [...conversations].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <Button
          onClick={handleCreateNew}
          className="w-full justify-start gap-2"
          variant="ghost"
        >
          <Plus className="w-4 h-4" />
          New Conversation
        </Button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {sortedConversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No conversations yet. Start a new one!
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {sortedConversations.map((conversation) => (
              <div
                key={conversation.id}
                className={clsx(
                  'group flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors',
                  currentConversationId === conversation.id
                    ? 'bg-primary-100 text-primary-900'
                    : 'hover:bg-gray-100'
                )}
                onClick={() => selectConversation(conversation.id)}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0 text-gray-500" />
                
                {editingId === conversation.id ? (
                  <div className="flex-1 flex items-center gap-1">
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveEdit();
                        if (e.key === 'Escape') handleCancelEdit();
                      }}
                      className="flex-1 text-sm bg-white border border-gray-300 rounded px-2 py-1"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveEdit}
                      className="p-1 text-green-600 hover:bg-green-100 rounded"
                    >
                      <Check className="w-3 h-3" />
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="p-1 text-gray-500 hover:bg-gray-100 rounded"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {conversation.title}
                    </p>
                    <p className="text-xs text-gray-500">
                      {conversation.messages.length} messages
                    </p>
                  </div>
                )}

                {editingId !== conversation.id && (
                  <div className="flex opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(conversation);
                      }}
                      className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(conversation.id, e)}
                      className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
