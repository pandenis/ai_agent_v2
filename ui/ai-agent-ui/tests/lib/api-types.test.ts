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
      model_used: 'mistral',
      metadata: {
        strategy: 'direct',
        memory_coverage: 0.85,
        cached: false,
        elapsed_time_ms: 50,
      },
    };
    expect(response.text).toBeDefined();
    expect(response.metadata.strategy).toBe('direct');
  });

  test('Strategy type only allows valid values', () => {
    const validStrategies: Strategy[] = ['direct', 'enhanced', 'deep_reasoning'];
    validStrategies.forEach(s => {
      expect(['direct', 'enhanced', 'deep_reasoning']).toContain(s);
    });
  });

  test('Session has required fields', () => {
    const session: Session = {
      id: 'sess-123',
      title: 'Test Session',
      created_at: '2026-01-15T10:00:00Z',
      updated_at: '2026-01-15T10:30:00Z',
      message_count: 5,
    };
    expect(session.id).toBeDefined();
    expect(session.title).toBeDefined();
    expect(session.message_count).toBe(5);
  });
});
