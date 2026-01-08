"""
E2E Integration Tests for API Endpoints.

These tests verify the full request → response cycle through the real API,
ensuring all components are properly wired together.

Purpose:
    - Prevent "hidden bypass" issues (like the 7-week orchestrator gap)
    - Verify endpoints work end-to-end, not just in isolation
    - Test real FastAPI app with TestClient

The Golden Rule: "If you can't curl it, it doesn't work"
These tests are the programmatic equivalent of curl verification.

Usage:
    pytest tests/integration/test_api_e2e.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpointE2E:
    """E2E tests for health check endpoint."""

    def test_health_endpoint_returns_healthy(self):
        """Test: GET /health returns healthy status.

        This is the simplest E2E test - verifies the API is running
        and responding correctly.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestAgentsEndpointsE2E:
    """E2E tests for agents endpoints."""

    def test_agents_status_returns_agent_dict(self):
        """Test: GET /agents/status returns dict of available agents.

        Verifies the agent registry is properly connected and
        returns agent configurations.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/agents/status")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "agents" in data
        assert "available_agents" in data
        assert "enabled_agents" in data
        assert "default_agent" in data

        agents = data["agents"]
        assert isinstance(agents, dict)
        assert len(agents) > 0  # At least one agent configured

        # Verify known agents exist
        expected_agents = ["groq", "mistral", "deepseek"]
        for agent_name in expected_agents:
            assert agent_name in agents, f"Expected agent '{agent_name}' not found"

        # Verify agent structure
        groq_agent = agents["groq"]
        assert "available" in groq_agent
        assert "capabilities" in groq_agent
        assert "enabled" in groq_agent
        assert isinstance(groq_agent["capabilities"], list)

    def test_agents_select_returns_best_agent(self):
        """Test: POST /agents/select returns best agent for task.

        Verifies agent selection logic works end-to-end.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v1/agents/select",
            json={
                "prompt": "Help me write Python code for sorting a list",
                "task_type": "code_analysis"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data
        assert "reasoning" in data
        assert data["confidence"] > 0  # Has some confidence score

class TestSessionsEndpointsE2E:
    """E2E tests for sessions endpoints."""

    def test_create_session_returns_session_id(self):
        """Test: POST /sessions creates a new session.

        Verifies session creation works end-to-end with database.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "agent_name" in data
        assert "created_at" in data
        assert data["agent_name"] == "mistral"
        assert len(data["session_id"]) == 36  # UUID format

    def test_list_sessions_returns_array(self):
        """Test: GET /sessions returns list of sessions.

        Verifies session listing works end-to-end.
        """
        # Arrange
        client = TestClient(app)

        # First create a session to ensure list is not empty
        client.post("/api/v1/sessions", json={"agent_name": "mistral"})

        # Act
        response = client.get("/api/v1/sessions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # At least one session exists

        # Verify session structure
        session = data[0]
        assert "session_id" in session
        assert "agent_name" in session
        assert "created_at" in session

    def test_get_session_by_id_returns_session(self):
        """Test: GET /sessions/{session_id} returns specific session.

        Verifies session retrieval by ID works end-to-end.
        """
        # Arrange
        client = TestClient(app)

        # Create a session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "groq"}
        )
        session_id = create_response.json()["session_id"]

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["agent_name"] == "groq"

    def test_get_session_not_found_returns_404(self):
        """Test: GET /sessions/{session_id} returns 404 for invalid ID.

        Verifies proper error handling for non-existent sessions.
        """
        # Arrange
        client = TestClient(app)
        fake_session_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = client.get(f"/api/v1/sessions/{fake_session_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_session_messages_returns_empty_list(self):
        """Test: GET /sessions/{session_id}/messages returns messages.

        Verifies session messages retrieval works end-to-end.
        New session should have empty messages list.
        """
        # Arrange
        client = TestClient(app)

        # Create a session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        session_id = create_response.json()["session_id"]

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}/messages")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0  # New session has no messages

    def test_get_session_facts_returns_empty_list(self):
        """Test: GET /sessions/{session_id}/facts returns facts.

        Verifies session facts retrieval works end-to-end.
        New session should have empty facts list.
        """
        # Arrange
        client = TestClient(app)

        # Create a session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        session_id = create_response.json()["session_id"]

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}/facts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "facts" in data
        assert "total" in data
        assert isinstance(data["facts"], list)
        assert data["total"] == 0  # New session has no facts

class TestMemoryEndpointsE2E:
    """E2E tests for memory endpoints."""

    def test_memory_stats_returns_statistics(self):
        """Test: GET /memory/stats returns memory statistics.

        Verifies memory service is connected and returns stats.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/memory/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_facts" in data
        assert isinstance(data["total_facts"], int)

    def test_memory_facts_returns_list(self):
        """Test: GET /memory/facts returns list of facts.

        Verifies memory facts retrieval works end-to-end.
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/memory/facts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        assert isinstance(data["facts"], list)