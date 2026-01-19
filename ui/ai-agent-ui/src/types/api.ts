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

export interface QueryAnalysis {
  complexity: 'simple' | 'medium' | 'complex';
  intent: string;
  topics: string[];
  entities: string[];
  query_type: string;
  confidence: number;
}

export interface OrchestrateResponse {
  text: string;
  model_used?: string;
  metadata: ResponseMetadata;
  query_analysis?: QueryAnalysis;
}

export interface Session {
  session_id: string;
  agent_name: string;
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

// Fact - matches actual backend format
export interface Fact {
  fact_id: string;
  text: string;
  importance: number;
  confidence: number;
  tags: string[];
  fact_type: string;
  source: string;
  created: string;
  updated: string;
  usage_count: number;
}

// Facts response wrapper
export interface FactsResponse {
  facts: Fact[];
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version?: string;
}

// Messages response wrapper
export interface MessagesResponse {
  session_id: string;
  messages: Message[];
  total: number;
}
