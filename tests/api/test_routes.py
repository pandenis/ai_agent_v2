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

    def test_select_agent_success(self):
        """Test: POST /agents/select returns selected agent."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": "What is the weather today?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data

    def test_select_agent_invalid_input_returns_400(self):
        """Test: POST /agents/select with invalid input returns 400."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": ""}  # Empty prompt
        )

        assert response.status_code == 400

    def test_select_agent_invalid_task_type_returns_400(self):
        """Test: POST /agents/select with invalid task_type returns 400."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": "Hello world", "task_type": "invalid_type"}
        )

        assert response.status_code == 400
        assert "Invalid task_type" in response.json()["detail"]

class TestSessionEndpoints:
    """Tests for /sessions/* endpoints."""

    def test_create_session_success(self):
        """Test: POST /sessions creates new session."""
        response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["agent_name"] == "mistral"

    def test_get_sessions_returns_list(self):
        """Test: GET /sessions returns list of sessions."""
        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_session_not_found_returns_404(self):
        """Test: GET /sessions/{id} with invalid id returns 404."""
        response = client.get("/api/v1/sessions/nonexistent-session-id")

        assert response.status_code == 404

    def test_get_session_success(self):
        """Test: GET /sessions/{id} returns session details."""
        # First create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "test-agent"}
        )
        session_id = create_response.json()["session_id"]

        # Then get it
        response = client.get(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    def test_get_session_messages_not_found_returns_404(self):
        """Test: GET /sessions/{id}/messages with invalid session returns 404."""
        response = client.get("/api/v1/sessions/nonexistent-id/messages")

        assert response.status_code == 404