"""
Smoke tests — run against the LIVE production server (port 8000).

Tag: @pytest.mark.smoke
These tests are intentionally read-only and leave zero side-effects.
"""
import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.smoke
def test_health_endpoint_returns_healthy():
    response = httpx.get(f"{BASE_URL}/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.smoke
def test_orchestrate_response_contains_strategy_field():
    """
    Regression guard: verify the IntelligentOrchestrator is wired into the
    request pipeline and not bypassed.

    Historical context: a 7-week hidden bug caused the Orchestrator to be
    completely skipped in production even though all unit tests passed.
    The presence of the "strategy" field in the response is the definitive
    signal that the Orchestrator ran — if it is absent, the bypass has
    re-occurred.
    """
    payload = {"query": "What is 2 + 2?", "session_id": "smoke-test-001"}
    response = httpx.post(
        f"{BASE_URL}/api/v1/orchestrate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60.0,
    )
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "strategy" in data["metadata"]
    assert data["metadata"]["strategy"] in ["direct", "enhanced", "deep_reasoning"]
