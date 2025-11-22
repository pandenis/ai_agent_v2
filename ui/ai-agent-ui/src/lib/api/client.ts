/**
 * API Client for AI Agent Backend
 * Handles all HTTP requests to FastAPI backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.237:8000/api/v1'

export interface ApiError {
  message: string
  status: number
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      if (!response.ok) {
        throw {
          message: `API Error: ${response.statusText}`,
          status: response.status,
        } as ApiError
      }

      return await response.json()
    } catch (error) {
      console.error('API Request failed:', error)
      throw error
    }
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
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for custom instances
export default ApiClient
