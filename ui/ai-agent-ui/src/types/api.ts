/**
 * API Types for AI Agent Backend
 * 
 * These types match the ACTUAL backend API responses.
 */

// ============ Request Types ============

export interface OrchestrateRequest {
  query: string;
  session_id: string;
  model_preference?: string;
}

export interface CreateSessionRequest {
  title?: string;
  agent_name?: string;
}

// ============ Response Types ============

export type Strategy = 'direct' | 'enhanced' | 'deep_reasoning';

export interface ResponseMetadata {
  strategy: Strategy;
  memory_coverage: number;
  cached: boolean;
  elapsed_time_ms: number;
  confidence?: number;
  sources?: string[];
  model_used?: string;
  cost_usd?: number;
  reasoning_depth?: number;
}

export interface OrchestrateResponse {
  text: string;
  model_used?: string;
  metadata: ResponseMetadata;
}

// Session - matches actual backend format
export interface Session {
  session_id: string;        // Backend uses session_id
  agent_name: string;        // Backend uses agent_name
  created_at: string;
  updated_at?: string;
  message_count: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  session_id: string;
  metadata?: Partial<ResponseMetadata>;
}

export interface Fact {
  id: string;
  content: string;
  importance: number;
  confidence: number;
  source: string;
  tags: string[];
  created_at: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version?: string;
}
