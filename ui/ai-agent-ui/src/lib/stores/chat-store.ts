/**
 * Chat Store - Manages chat messages and state
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Strategy } from '@/types/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    strategy?: Strategy;
    cached?: boolean;
    elapsed_time_ms?: number;
    memory_coverage?: number;
    confidence?: number;
  };
}

interface ChatState {
  messages: ChatMessage[];
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;

  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set) => ({
      messages: [],
      currentSessionId: null,
      isLoading: false,
      error: null,

      addMessage: (message) =>
        set(
          (state) => ({
            messages: [
              ...state.messages,
              {
                ...message,
                id: crypto.randomUUID(),
                timestamp: new Date(),
              },
            ],
            error: null,
          }),
          false,
          'addMessage'
        ),

      setMessages: (messages) =>
        set({ messages }, false, 'setMessages'),

      setSession: (sessionId) =>
        set(
          {
            currentSessionId: sessionId,
            messages: [],
            error: null,
          },
          false,
          'setSession'
        ),

      setLoading: (loading) =>
        set({ isLoading: loading }, false, 'setLoading'),

      setError: (error) =>
        set({ error, isLoading: false }, false, 'setError'),

      clearMessages: () =>
        set({ messages: [] }, false, 'clearMessages'),
    }),
    { name: 'chat-store' }
  )
);
