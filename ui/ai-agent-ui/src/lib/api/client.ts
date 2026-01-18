/**
 * API Client for AI Agent Backend
 */
import type {
  OrchestrateRequest,
  OrchestrateResponse,
  Session,
  CreateSessionRequest,
  Message,
  Fact,
  FactsResponse,
  MessagesResponse,
  HealthResponse,
} from '@/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Types for new endpoints
export interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
  size: number;
  max_size: number;
  estimated_bytes?: number;
  strategy_distribution?: Record<string, number>;
}

export interface SessionStats {
  session_id: string;
  message_count: number;
  user_messages: number;
  assistant_messages: number;
  agent_name: string;
  created_at: string | null;
}

export const api = {
  orchestrate: (req: OrchestrateRequest): Promise<OrchestrateResponse> => {
    return request<OrchestrateResponse>('/api/v1/orchestrate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  getSessions: (): Promise<Session[]> => {
    return request<Session[]>('/api/v1/sessions');
  },

  getSession: (sessionId: string): Promise<Session> => {
    return request<Session>(`/api/v1/sessions/${sessionId}`);
  },

  createSession: (req?: CreateSessionRequest): Promise<Session> => {
    return request<Session>('/api/v1/sessions', {
      method: 'POST',
      body: JSON.stringify(req || {}),
    });
  },

  renameSession: (sessionId: string, newName: string): Promise<Session> => {
    return request<Session>(`/api/v1/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ agent_name: newName }),
    });
  },

  deleteSession: (sessionId: string): Promise<void> => {
    return request<void>(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  getMessages: async (sessionId: string): Promise<Message[]> => {
    const response = await request<MessagesResponse>(`/api/v1/sessions/${sessionId}/messages`);
    return response.messages;
  },

  getFacts: async (sessionId?: string): Promise<Fact[]> => {
    const endpoint = sessionId
      ? `/api/v1/memory/facts?session_id=${sessionId}`
      : '/api/v1/memory/facts';
    const response = await request<FactsResponse>(endpoint);
    return response.facts;
  },

  health: (): Promise<HealthResponse> => {
    return request<HealthResponse>('/api/v1/health');
  },

  // New: Cache statistics
  getCacheStats: (): Promise<CacheStats> => {
    return request<CacheStats>('/api/v1/system/cache-stats');
  },

  // New: Session statistics
  getSessionStats: (sessionId: string): Promise<SessionStats> => {
    return request<SessionStats>(`/api/v1/sessions/${sessionId}/stats`);
  },
};
