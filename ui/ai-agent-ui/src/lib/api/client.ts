/**
 * API Client for AI Agent Backend
 * 
 * Handles all communication with the backend API.
 * Base URL defaults to localhost:8000 for development.
 */

import type {
  OrchestrateRequest,
  OrchestrateResponse,
  Session,
  CreateSessionRequest,
  Message,
  Fact,
  HealthResponse,
} from '@/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
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

    return response.json();
  }

  // ============ Orchestrate ============

  async orchestrate(request: OrchestrateRequest): Promise<OrchestrateResponse> {
    return this.request<OrchestrateResponse>('/api/v1/orchestrate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ============ Sessions ============

  async getSessions(): Promise<Session[]> {
    return this.request<Session[]>('/api/v1/sessions');
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/api/v1/sessions/${sessionId}`);
  }

  async createSession(request?: CreateSessionRequest): Promise<Session> {
    return this.request<Session>('/api/v1/sessions', {
      method: 'POST',
      body: JSON.stringify(request || {}),
    });
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.request<void>(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // ============ Messages ============

  async getMessages(sessionId: string): Promise<Message[]> {
    return this.request<Message[]>(`/api/v1/sessions/${sessionId}/messages`);
  }

  // ============ Memory / Facts ============

  async getFacts(sessionId?: string): Promise<Fact[]> {
    const endpoint = sessionId
      ? `/api/v1/memory/facts?session_id=${sessionId}`
      : '/api/v1/memory/facts';
    return this.request<Fact[]>(endpoint);
  }

  // ============ Health ============

  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing
export { ApiClient };
