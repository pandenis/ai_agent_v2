import { describe, test, expect } from 'vitest';
import type { 
  OrchestrateRequest, 
  OrchestrateResponse, 
  Session,
  Strategy 
} from '@/types/api';

describe('API Types', () => {
  test('OrchestrateRequest has required fields', () => {
    const request: OrchestrateRequest = {
      query: 'What is my name?',
      session_id: 'test-123',
    };
    expect(request.query).toBeDefined();
    expect(request.session_id).toBeDefined();
  });

  test('OrchestrateResponse has metadata with strategy', () => {
    const response: OrchestrateResponse = {
      text: 'Your name is Denis',
      metadata: {
        strategy: 'enhanced',
        memory_coverage: 0.85,
        cached: false,
        elapsed_time_ms: 50,
        confidence: 0.8,
      },
    };
    expect(response.text).toBeDefined();
    expect(response.metadata.strategy).toBe('enhanced');
  });

  test('Strategy type only allows valid values', () => {
    const validStrategies: Strategy[] = ['direct', 'enhanced', 'deep_reasoning'];
    validStrategies.forEach(s => {
      expect(['direct', 'enhanced', 'deep_reasoning']).toContain(s);
    });
  });

  test('Session matches backend format', () => {
    const session: Session = {
      session_id: 'sess-123',       // Not 'id'
      agent_name: 'mistral',        // Not 'title'
      created_at: '2026-01-15T10:00:00Z',
      message_count: 5,
    };
    expect(session.session_id).toBeDefined();
    expect(session.agent_name).toBeDefined();
    expect(session.message_count).toBe(5);
  });
});
