"""
Tests for API routes.

Covers all endpoints in app/api/routes.py
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_returns_healthy(self):
        """Test: GET /health returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestAgentsEndpoints:
    """Tests for /agents/* endpoints."""

    def test_get_agents_status_returns_200(self):
        """Test: GET /agents/status returns agent statuses."""
        response = client.get("/api/v1/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data or "status" in data