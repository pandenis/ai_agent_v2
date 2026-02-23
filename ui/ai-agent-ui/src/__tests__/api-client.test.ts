import { vi, describe, test, expect, beforeEach } from 'vitest';

// Must run before the static import below so API_BASE is initialised correctly.
vi.hoisted(() => {
  process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/api/v1';
});

import { api } from '@/lib/api/client';

describe('API Client — no duplicate /api/v1 prefix', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test('test_orchestrate_url_has_no_duplicate_prefix', async () => {
    // Arrange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          text: 'ok',
          model_used: 'm',
          metadata: { strategy: 'direct', memory_coverage: 0, cached: false, elapsed_time_ms: 0 },
        }),
    });

    // Act
    await api.orchestrate({ query: 'hello', session_id: 's1' });

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/orchestrate',
      expect.any(Object),
    );
  });

  test('test_get_sessions_url_has_no_duplicate_prefix', async () => {
    // Arrange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });

    // Act
    await api.getSessions();

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/sessions',
      expect.any(Object),
    );
  });

  test('test_get_system_health_url_has_no_duplicate_prefix', async () => {
    // Arrange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'healthy' }),
    });

    // Act
    await api.getHealth();

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/health',
      expect.any(Object),
    );
  });
});
