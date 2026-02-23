import { describe, test, expect, vi, beforeEach } from 'vitest';
import { api, ApiClient } from '@/lib/api/client';

describe('API Client', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('orchestrate', () => {
    test('sends correct request format', async () => {
      const mockResponse = {
        text: 'Hello Denis',
        model_used: 'mistral',
        metadata: {
          strategy: 'direct',
          memory_coverage: 0.9,
          cached: false,
          elapsed_time_ms: 50,
        },
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.orchestrate({
        query: 'What is my name?',
        session_id: 'test-123',
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/orchestrate'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      expect(result.text).toBe('Hello Denis');
      expect(result.metadata.strategy).toBe('direct');
    });

    test('throws error on API failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      });

      await expect(
        api.orchestrate({ query: 'test', session_id: '123' })
      ).rejects.toThrow('API Error: 500');
    });
  });

  describe('getSessions', () => {
    test('fetches sessions list', async () => {
      const mockSessions = [
        { id: '1', title: 'Session 1', created_at: '', updated_at: '', message_count: 5 },
        { id: '2', title: 'Session 2', created_at: '', updated_at: '', message_count: 3 },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSessions),
      });

      const result = await api.getSessions();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions'),
        expect.any(Object)
      );
      expect(result).toHaveLength(2);
    });
  });

  describe('health', () => {
    test('returns health status', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' }),
      });

      const result = await api.health();
      expect(result.status).toBe('healthy');
    });
  });

  describe('createSession', () => {
    test('creates new session', async () => {
      const mockSession = {
        id: 'new-123',
        title: 'New Session',
        created_at: '2026-01-15T10:00:00Z',
        updated_at: '2026-01-15T10:00:00Z',
        message_count: 0,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSession),
      });

      const result = await api.createSession({ title: 'New Session' });

      expect(result.id).toBe('new-123');
      expect(result.title).toBe('New Session');
    });
  });
});
