/**
 * API Types for AI Agent Backend
 * 
 * These types match the backend API responses.
 * See: /api/v1/orchestrate, /api/v1/sessions, etc.
 */

// ============ Request Types ============

export interface OrchestrateRequest {
  query: string;
  session_id: string;
  model_preference?: string;
}

export interface CreateSessionRequest {
  title?: string;
}

// ============ Response Types ============

export type Strategy = 'direct' | 'enhanced' | 'deep_reasoning';

export interface ResponseMetadata {
  strategy: Strategy;
  memory_coverage: number;
  cached: boolean;
  elapsed_time_ms: number;
  sources?: string[];
  model_used?: string;
}

export interface OrchestrateResponse {
  text: string;
  model_used: string;
  metadata: ResponseMetadata;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
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
