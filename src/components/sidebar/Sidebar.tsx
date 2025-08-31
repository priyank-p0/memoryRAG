import React, { useState } from 'react';
import { Settings, X } from 'lucide-react';
import { ConversationList } from './ConversationList';
import { ModelSelector } from '../settings/ModelSelector';
import { Button } from '../ui/Button';
import { useChatStore } from '../../store/chatStore';
import { clsx } from 'clsx';

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useChatStore();
  const [activeTab, setActiveTab] = useState<'conversations' | 'settings'>('conversations');

  return (
    <>
      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          'fixed left-0 top-0 z-50 h-full w-80 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h1 className="text-xl font-semibold text-gray-900">
            Multi-Model Chat
          </h1>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="lg:hidden"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('conversations')}
            className={clsx(
              'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'conversations'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Conversations
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={clsx(
              'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'settings'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <Settings className="w-4 h-4 inline mr-1" />
            Settings
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'conversations' ? (
            <ConversationList />
          ) : (
            <div className="p-4 overflow-y-auto h-full">
              <ModelSelector />
            </div>
          )}
        </div>
      </div>
    </>
  );
};
