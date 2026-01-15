/**
 * Chat Store - Manages chat messages and state
 * 
 * Uses Zustand for simple, performant state management.
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
  // State
  messages: ChatMessage[];
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set) => ({
      // Initial state
      messages: [],
      currentSessionId: null,
      isLoading: false,
      error: null,

      // Actions
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
