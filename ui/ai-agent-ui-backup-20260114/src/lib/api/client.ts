/**
 * API Client for AI Agent Backend
 * Handles all HTTP requests to FastAPI backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.237:8000/api/v1'

export interface ApiError {
  message: string
  status: number
}

// Import types
import { Session, SessionMessages, SessionFacts } from '@/types'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
  endpoint: string,
  options?: RequestInit,
  retries: number = 2
): Promise<T> {
  const url = `${this.baseUrl}${endpoint}`

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      if (!response.ok) {
        // Don't retry on 4xx errors (client errors)
        if (response.status >= 400 && response.status < 500) {
          throw {
            message: `API Error: ${response.statusText}`,
            status: response.status,
          } as ApiError
        }

        // Retry on 5xx errors (server errors)
        if (attempt < retries) {
          console.log(`Retry attempt ${attempt + 1}/${retries} for ${endpoint}`)
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
          continue
        }

        throw {
          message: `API Error: ${response.statusText}`,
          status: response.status,
        } as ApiError
      }

      return await response.json()
    } catch (error) {
      // Network errors - retry
      if (attempt < retries && error instanceof TypeError) {
        console.log(`Network error, retry ${attempt + 1}/${retries}`)
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
        continue
      }

      console.error('API Request failed:', error)
        throw error
    }
  }

        throw new Error('Max retries exceeded')
    }

  // Health check
  async health() {
    return this.request<{ status: string }>('/health')
  }

  // Memory endpoints
  async getMemoryStats() {
    return this.request<{
      total_facts: number
      facts_by_type: Record<string, number>
      avg_importance: number
    }>('/memory/stats')
  }

  async getMemoryFacts(limit: number = 10, offset: number = 0) {
    return this.request<{
      facts: Array<{
        fact_id: string
        text: string
        importance: number
        confidence: number
        tags: string[]
        fact_type: string
        source: string
        created: string
      }>
      total: number
      limit: number
      offset: number
      has_more: boolean
    }>(`/memory/facts?limit=${limit}&offset=${offset}`)
  }

  // Chat endpoint
  async sendMessage(data: {
    message: string
    session_id: string
    agent_name?: string
    include_memory?: boolean
  }) {
    return this.request<{
      response: string
      session_id: string
      agent_used: string
      sources_used: string[]
      tokens_used: number
      timestamp: string
    }>('/chat/enhanced', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ========================================
  // SESSION MANAGEMENT (NEW)
  // ========================================

  async getSessions(limit = 50, skip = 0): Promise<Session[]> {
    return this.request<Session[]>(`/sessions?limit=${limit}&skip=${skip}`)
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`)
  }

  async getSessionMessages(sessionId: string): Promise<SessionMessages> {
    return this.request<SessionMessages>(`/sessions/${sessionId}/messages`)
  }

  async getSessionFacts(sessionId: string): Promise<SessionFacts> {
    return this.request<SessionFacts>(`/sessions/${sessionId}/facts`)
  }

  async createSession(agentName: string = 'mistral'): Promise<Session> {
    return this.request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ agent_name: agentName })
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for custom instances
export default ApiClient