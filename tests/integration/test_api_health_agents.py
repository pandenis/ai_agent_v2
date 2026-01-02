"""
Integration tests for Health and Agents API endpoints.

Tests:
- GET /health
- GET /agents/status
- POST /agents/select
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_returns_healthy(self, client):
        """Test: GET /health returns healthy status."""
        # Act
        response = client.get("/api/v1/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAgentsStatusEndpoint:
    """Tests for /agents/status endpoint."""

    def test_get_agents_status_success(self, client, mock_agent_service):
        """Test: GET /agents/status returns agent status."""
        # Arrange
        with patch('app.api.routes.get_agent_service', return_value=mock_agent_service):
            with patch('app.api.deps.get_agent_service', return_value=mock_agent_service):
                # Act
                response = client.get("/api/v1/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data or "default_agent" in data


class TestAgentsSelectEndpoint:
    """Tests for /agents/select endpoint."""

    def test_select_agent_success(self, client):
        """Test: POST /agents/select returns selected agent."""
        # Arrange
        request_data = {
            "prompt": "Write a Python function to calculate fibonacci",
            "task_type": "code_analysis"
        }
        
        # Act
        response = client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data

    def test_select_agent_invalid_task_type(self, client):
        """Test: POST /agents/select with invalid task_type returns 400."""
        # Arrange
        request_data = {
            "prompt": "Test prompt",
            "task_type": "invalid_task_type"
        }
        
        # Act
        response = client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 400
        assert "Invalid task_type" in response.json()["detail"]

    def test_select_agent_empty_prompt(self, client):
        """Test: POST /agents/select with empty prompt returns 400."""
        # Arrange
        request_data = {
            "prompt": "",
            "task_type": "general_chat"
        }
        
        # Act
        response = client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 400

    def test_select_agent_without_task_type(self, client):
        """Test: POST /agents/select without task_type uses default."""
        # Arrange
        request_data = {
            "prompt": "What is the weather today?"
        }
        
        # Act
        response = client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
