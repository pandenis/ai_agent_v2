'use client';

import React, { useState, useEffect } from 'react';
import MessageList from '@/components/features/MessageList';
import ChatInput from '@/components/features/ChatInput';
import AgentSelector from '@/components/features/AgentSelector';
import { type Message } from '@/types';
import { apiClient } from '@/lib/api/client';

interface ChatInterfaceProps {
  sessionId: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('groq');
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(true);

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
    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
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

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to send message'}`,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Header with Agent Selector */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-950">
        <div>
          <h2 className="text-lg font-semibold text-slate-200">
            Session: {sessionId.slice(0, 8)}...
          </h2>
        </div>

        <AgentSelector
          selectedAgent={selectedAgent}
          onSelect={setSelectedAgent}
          disabled={loading}
        />
      </div>

      {/* Messages */}
      {loadingMessages ? (
        <div className="flex-1 flex items-center justify-center text-slate-400">
          Loading messages...
        </div>
      ) : (
        <MessageList messages={messages} loading={loading} />
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={loading}
        placeholder={loading ? 'AI is thinking...' : 'Type your message...'}
      />
    </div>
  );
};
