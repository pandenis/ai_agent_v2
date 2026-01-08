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