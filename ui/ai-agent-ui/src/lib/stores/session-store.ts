/**
 * Session Store - Manages sessions list and active session
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Session } from '@/types/api';

interface SessionState {
  // State
  sessions: Session[];
  activeSessionId: string | null;
  isLoading: boolean;

  // Actions
  setSessions: (sessions: Session[]) => void;
  setActiveSession: (id: string | null) => void;
  addSession: (session: Session) => void;
  updateSession: (id: string, updates: Partial<Session>) => void;
  removeSession: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useSessionStore = create<SessionState>()(
  devtools(
    (set) => ({
      // Initial state
      sessions: [],
      activeSessionId: null,
      isLoading: false,

      // Actions
      setSessions: (sessions) =>
        set({ sessions }, false, 'setSessions'),

      setActiveSession: (id) =>
        set({ activeSessionId: id }, false, 'setActiveSession'),

      addSession: (session) =>
        set(
          (state) => ({
            sessions: [session, ...state.sessions],
          }),
          false,
          'addSession'
        ),

      updateSession: (id, updates) =>
        set(
          (state) => ({
            sessions: state.sessions.map((s) =>
              s.session_id === id ? { ...s, ...updates } : s
            ),
          }),
          false,
          'updateSession'
        ),

      removeSession: (id) =>
        set(
          (state) => ({
            sessions: state.sessions.filter((s) => s.session_id !== id),
            activeSessionId:
              state.activeSessionId === id ? null : state.activeSessionId,
          }),
          false,
          'removeSession'
        ),

      setLoading: (loading) =>
        set({ isLoading: loading }, false, 'setLoading'),
    }),
    { name: 'session-store' }
  )
);
