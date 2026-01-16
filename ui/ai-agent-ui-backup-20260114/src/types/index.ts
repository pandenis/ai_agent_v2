/**
 * Common TypeScript types for AI Agent UI
 */

// API Response types
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  status: number
}

// Chat types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  agent_used?: string
  sources?: string[]
  tokens_used?: number | null
}

export interface ChatSession {
  session_id: string
  agent_name: string
  created_at: string
  messages?: Message[]
}

// Memory/Fact types
export interface Fact {
  fact_id: string
  text: string
  importance: number
  confidence: number
  tags: string[]
  fact_type: 'static' | 'event' | 'preference'
  source: string
  created: string
  updated: string
}

export interface MemoryStats {
  total_facts: number
  facts_by_type: Record<string, number>
  avg_importance: number
}

// Component prop types
export interface BaseProps {
  className?: string
  children?: React.ReactNode
}

// Session types
export interface Session {
  session_id: string
  agent_name: string
  created_at: string
  last_activity?: string
  is_active?: boolean
  message_count?: number
}

export interface SessionMessages {
  session_id: string
  messages: Message[]
  total: number
}

export interface SessionFact {
  fact_id: string
  text: string
  fact_type: string
  importance: number
  confidence: number
  created: string
  tags: string[]
}

export interface SessionFacts {
  session_id: string
  facts: SessionFact[]
  total: number
}

export type Variant = 'primary' | 'secondary' | 'accent' | 'ghost'
export type Size = 'sm' | 'md' | 'lg'

