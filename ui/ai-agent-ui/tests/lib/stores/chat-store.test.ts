import { describe, test, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/lib/stores/chat-store';

describe('ChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      currentSessionId: null,
      isLoading: false,
      error: null,
    });
  });

  describe('addMessage', () => {
    test('adds message with auto-generated id and timestamp', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'Hello',
      });

      const { messages } = useChatStore.getState();
      expect(messages).toHaveLength(1);
      expect(messages[0].id).toBeDefined();
      expect(messages[0].timestamp).toBeInstanceOf(Date);
      expect(messages[0].role).toBe('user');
      expect(messages[0].content).toBe('Hello');
    });

    test('preserves existing messages', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'First' });
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Second' });

      const { messages } = useChatStore.getState();
      expect(messages).toHaveLength(2);
      expect(messages[0].content).toBe('First');
      expect(messages[1].content).toBe('Second');
    });

    test('includes metadata if provided', () => {
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: 'Response',
        metadata: { strategy: 'direct', cached: true, elapsed_time_ms: 50 },
      });

      const { messages } = useChatStore.getState();
      expect(messages[0].metadata?.strategy).toBe('direct');
      expect(messages[0].metadata?.cached).toBe(true);
    });
  });

  describe('setSession', () => {
    test('sets sessionId and clears messages', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'Old' });
      useChatStore.getState().setSession('new-session-123');

      const state = useChatStore.getState();
      expect(state.currentSessionId).toBe('new-session-123');
      expect(state.messages).toHaveLength(0);
    });
  });

  describe('setLoading', () => {
    test('sets loading state', () => {
      useChatStore.getState().setLoading(true);
      expect(useChatStore.getState().isLoading).toBe(true);

      useChatStore.getState().setLoading(false);
      expect(useChatStore.getState().isLoading).toBe(false);
    });
  });

  describe('setError', () => {
    test('sets and clears error', () => {
      useChatStore.getState().setError('Something went wrong');
      expect(useChatStore.getState().error).toBe('Something went wrong');

      useChatStore.getState().setError(null);
      expect(useChatStore.getState().error).toBeNull();
    });
  });

  describe('clearMessages', () => {
    test('clears all messages', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'Test' });
      useChatStore.getState().clearMessages();

      expect(useChatStore.getState().messages).toHaveLength(0);
    });
  });
});
