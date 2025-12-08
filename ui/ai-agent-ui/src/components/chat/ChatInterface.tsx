'use client';

import React, { useState, useEffect } from 'react';
import MessageList from '@/components/features/MessageList';
import { TypingIndicator } from '@/components/ui/TypingIndicator'
import ChatInput from '@/components/features/ChatInput';
import { MemoryPanel } from '@/components/features/MemoryPanel';
import AgentSelector from '@/components/features/AgentSelector';
import { type Message } from '@/types';
import { apiClient } from '@/lib/api/client';
import toast from 'react-hot-toast';

interface ChatInterfaceProps {
  sessionId: string;
  onLoadingChange?: (loading: boolean) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId, onLoadingChange }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAiTyping, setIsAiTyping] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('groq');
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [isMemoryPanelOpen, setIsMemoryPanelOpen] = useState(false);

  // Load messages when sessionId changes
  useEffect(() => {
    loadSessionMessages();
  }, [sessionId]);

  const loadSessionMessages = async () => {
    try {
      setLoadingMessages(true);
      const data = await apiClient.getSessionMessages(sessionId);
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    // Add user message

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    onLoadingChange?.(true);

    try {
      setIsAiTyping(true)

      // Call API
      const response = await apiClient.sendMessage({
        message: content,
        session_id: sessionId,
        agent_name: selectedAgent,
        include_memory: true,
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Failed to send message:', error);

      // Show toast notification
      toast.error(error.message || 'Failed to send message. Please try again.');
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to send message'}`,
        timestamp: new Date().toISOString(),
      };

    } finally {
        setIsAiTyping(false);
        setLoading(false);
        onLoadingChange?.(false);

    }
  };

  return (
  <div className="flex h-full">
    {/* Main Chat Area */}
    <div className={`flex flex-col bg-slate-900 transition-all duration-300 ${
      isMemoryPanelOpen ? 'w-2/3' : 'w-full'
    }`}>
      {/* Header with Agent Selector */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-950">
        <div>
          <h2 className="text-lg font-semibold text-slate-200">
            Session: {sessionId.slice(0, 8)}...
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMemoryPanelOpen(!isMemoryPanelOpen)}
            className={`px-3 py-1.5 text-sm rounded ${
              isMemoryPanelOpen
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {isMemoryPanelOpen ? '✕ Memory' : '📝 Memory'}
          </button>
          <AgentSelector
            selectedAgent={selectedAgent}
            onSelect={setSelectedAgent}
            disabled={loading}
          />
        </div>
      </div>

      {/* Messages */}
      {loadingMessages ? (
        <div className="flex-1 flex items-center justify-center text-slate-400">
          Loading messages...
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <MessageList messages={messages} loading={loading} />
          {isAiTyping && <TypingIndicator />}
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={loading}
        placeholder={loading ? 'AI is thinking...' : 'Type your message...'}
      />
    </div>

    {/* Memory Panel */}
    {isMemoryPanelOpen && (
      <div className="w-1/3 border-l border-slate-700 bg-slate-950">
        <MemoryPanel
          sessionId={sessionId}
          isOpen={isMemoryPanelOpen}
          onClose={() => setIsMemoryPanelOpen(false)}
        />
      </div>
    )}
  </div>
);
};
