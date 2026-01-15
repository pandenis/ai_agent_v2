import { describe, test, expect, beforeEach } from 'vitest';
import { useSessionStore } from '@/lib/stores/session-store';

describe('SessionStore', () => {
  beforeEach(() => {
    useSessionStore.setState({
      sessions: [],
      activeSessionId: null,
      isLoading: false,
    });
  });

  describe('setSessions', () => {
    test('sets sessions list', () => {
      const sessions = [
        { session_id: '1', agent_name: 'mistral', created_at: '', message_count: 5 },
        { session_id: '2', agent_name: 'groq', created_at: '', message_count: 3 },
      ];

      useSessionStore.getState().setSessions(sessions);

      expect(useSessionStore.getState().sessions).toHaveLength(2);
      expect(useSessionStore.getState().sessions[0].agent_name).toBe('mistral');
    });
  });

  describe('setActiveSession', () => {
    test('sets active session id', () => {
      useSessionStore.getState().setActiveSession('session-123');
      expect(useSessionStore.getState().activeSessionId).toBe('session-123');
    });

    test('can set to null', () => {
      useSessionStore.getState().setActiveSession('session-123');
      useSessionStore.getState().setActiveSession(null);
      expect(useSessionStore.getState().activeSessionId).toBeNull();
    });
  });

  describe('addSession', () => {
    test('adds session to beginning of list', () => {
      useSessionStore.getState().setSessions([
        { session_id: '1', agent_name: 'old', created_at: '', message_count: 0 },
      ]);

      useSessionStore.getState().addSession({
        session_id: '2',
        agent_name: 'new',
        created_at: '',
        message_count: 0,
      });

      const { sessions } = useSessionStore.getState();
      expect(sessions[0].agent_name).toBe('new');
      expect(sessions).toHaveLength(2);
    });
  });

  describe('removeSession', () => {
    test('removes session from list', () => {
      useSessionStore.getState().setSessions([
        { session_id: '1', agent_name: 'first', created_at: '', message_count: 0 },
        { session_id: '2', agent_name: 'second', created_at: '', message_count: 0 },
      ]);

      useSessionStore.getState().removeSession('1');

      const { sessions } = useSessionStore.getState();
      expect(sessions).toHaveLength(1);
      expect(sessions[0].session_id).toBe('2');
    });

    test('clears activeSessionId if removed session was active', () => {
      useSessionStore.getState().setSessions([
        { session_id: '1', agent_name: 'test', created_at: '', message_count: 0 },
      ]);
      useSessionStore.getState().setActiveSession('1');
      useSessionStore.getState().removeSession('1');

      expect(useSessionStore.getState().activeSessionId).toBeNull();
    });
  });
});
