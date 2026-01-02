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

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client):
        """Test: GET /health returns healthy status."""
        # Act
        response = await client.get("/api/v1/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAgentsStatusEndpoint:
    """Tests for /agents/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_agents_status_success(self, client):
        """Test: GET /agents/status returns agent status."""
        # Act
        response = await client.get("/api/v1/agents/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data or "default_agent" in data


class TestAgentsSelectEndpoint:
    """Tests for /agents/select endpoint."""

    @pytest.mark.asyncio
    async def test_select_agent_success(self, client):
        """Test: POST /agents/select returns selected agent."""
        # Arrange
        request_data = {
            "prompt": "Write a Python function to calculate fibonacci",
            "task_type": "code_analysis"
        }
        
        # Act
        response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    async def test_select_agent_invalid_task_type(self, client):
        """Test: POST /agents/select with invalid task_type returns 400."""
        # Arrange
        request_data = {
            "prompt": "Test prompt",
            "task_type": "invalid_task_type"
        }
        
        # Act
        response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 400
        assert "Invalid task_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_select_agent_empty_prompt(self, client):
        """Test: POST /agents/select with empty prompt returns 400."""
        # Arrange
        request_data = {
            "prompt": "",
            "task_type": "general_chat"
        }
        
        # Act
        response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_select_agent_without_task_type(self, client):
        """Test: POST /agents/select without task_type uses default."""
        # Arrange
        request_data = {
            "prompt": "What is the weather today?"
        }
        
        # Act
        response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestAgentsSelectEdgeCases:
    """Additional edge case tests for /agents/select endpoint."""

    @pytest.mark.asyncio
    async def test_select_agent_config_not_found(self, client):
        """Test: POST /agents/select returns 404 when agent config not found."""
        # Arrange
        request_data = {
            "prompt": "Test prompt for agent selection"
        }
        
        # Mock agent_service to return unknown agent and registry to return None
        with patch('app.api.routes.AgentService') as mock_service_class:
            mock_instance = MagicMock()
            mock_instance.select_best_agent_for_task = AsyncMock(return_value="nonexistent_agent")
            mock_service_class.return_value = mock_instance
            
            with patch('app.api.routes.agent_registry') as mock_registry:
                mock_registry.get_agent_config.return_value = None
                
                # Act
                response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 404
        assert "No suitable agent found" in response.json()["detail"]
