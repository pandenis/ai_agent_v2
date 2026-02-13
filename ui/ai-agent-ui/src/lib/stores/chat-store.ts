/**
 * Chat Store - Manages chat messages and state
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Strategy, QueryAnalysis } from '@/types/api';

// UUID fallback for browsers without crypto.randomUUID
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export interface ResponseMetadata {
  strategy?: Strategy;
  cached?: boolean;
  elapsed_time_ms?: number;
  memory_coverage?: number;
  confidence?: number;
  cost_usd?: number;
  reasoning_depth?: number;
  sources?: string[];
  query_analysis?: QueryAnalysis;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: ResponseMetadata;
}

interface ChatState {
  messages: ChatMessage[];
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;
  lastMetadata: ResponseMetadata | null;
  
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
  setLastMetadata: (metadata: ResponseMetadata | null) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set) => ({
      messages: [],
      currentSessionId: null,
      isLoading: false,
      error: null,
      lastMetadata: null,

      addMessage: (message) =>
        set(
          (state) => {
            // If this is an assistant message with metadata, also update lastMetadata
            const newLastMetadata = message.role === 'assistant' && message.metadata 
              ? message.metadata 
              : state.lastMetadata;
            
            return {
              messages: [
                ...state.messages,
                {
                  ...message,
                  id: generateUUID(),
                  timestamp: new Date(),
                },
              ],
              lastMetadata: newLastMetadata,
              error: null,
            };
          },
          false,
          'addMessage'
        ),

      setMessages: (messages) =>
        set(
          (state) => {
            // Find the last assistant message with metadata
            const lastAssistantMsg = [...messages]
              .reverse()
              .find(m => m.role === 'assistant' && m.metadata);
            
            return {
              messages,
              lastMetadata: lastAssistantMsg?.metadata || state.lastMetadata,
            };
          },
          false,
          'setMessages'
        ),

      setSession: (sessionId) =>
        set(
          {
            currentSessionId: sessionId,
            messages: [],
            lastMetadata: null,
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
        set({ messages: [], lastMetadata: null }, false, 'clearMessages'),

      setLastMetadata: (metadata) =>
        set({ lastMetadata: metadata }, false, 'setLastMetadata'),
    }),
    { name: 'chat-store' }
  )
);
