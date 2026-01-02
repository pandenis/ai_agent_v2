"""
Tests for AgentService class.

This module tests:
- Response generation with various agents
- Input validation
- Fallback behavior
- Agent status reporting
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.agent_service import AgentService
from app.core.agent_config import TaskType


class TestAgentServiceInit:
    """Tests for AgentService initialization."""

    def test_initialization(self):
        """Test: AgentService initializes with default agent."""
        # Act
        service = AgentService()
        
        # Assert
        assert service.default_agent == "mistral"
        assert service.factory is not None


class TestAgentServiceGenerateResponse:
    """Tests for AgentService.generate_response()."""

    @pytest.mark.asyncio
    async def test_generate_response_invalid_input(self):
        """Test: generate_response() returns error for invalid input."""
        # Arrange
        service = AgentService()
        
        # Act - empty prompt should be invalid
        result = await service.generate_response("")
        
        # Assert
        assert result["status"] == "error"
        assert "agent" in result

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test: generate_response() returns successful response."""
        # Arrange
        service = AgentService()
        
        mock_agent = Mock()
        mock_agent.health_check = AsyncMock(return_value=True)
        mock_agent.generate = AsyncMock(return_value={
            "status": "success",
            "response": "Test response",
            "tokens": 10
        })
        mock_agent.config = Mock()
        mock_agent.config.agent_type = Mock()
        mock_agent.config.agent_type.value = "local_ollama"
        mock_agent.config.capabilities = []
        
        with patch.object(service.factory, 'create_agent', return_value=mock_agent):
            # Act
            result = await service.generate_response("Hello, how are you?")
        
        # Assert
        assert result["status"] == "success"
        assert result["response"] == "Test response"
        assert "agent_name" in result

    @pytest.mark.asyncio
    async def test_generate_response_agent_not_available(self):
        """Test: generate_response() falls back when agent unavailable."""
        # Arrange
        service = AgentService()
        
        with patch.object(service.factory, 'create_agent', return_value=None):
            with patch.object(service, '_fallback_response', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = {
                    "status": "error",
                    "response": "Fallback response",
                    "fallback": True
                }
                
                # Act
                result = await service.generate_response("Hello")
        
        # Assert
        assert result["fallback"] is True
        mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_health_check_fails(self):
        """Test: generate_response() falls back when health check fails."""
        # Arrange
        service = AgentService()
        
        mock_agent = Mock()
        mock_agent.health_check = AsyncMock(return_value=False)
        
        with patch.object(service.factory, 'create_agent', return_value=mock_agent):
            with patch.object(service, '_fallback_response', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = {
                    "status": "error",
                    "response": "Fallback",
                    "fallback": True,
                    "fallback_reason": "Agent health check failed"
                }
                
                # Act
                result = await service.generate_response("Hello")
        
        # Assert
        assert result["fallback"] is True
        assert "health check" in result["fallback_reason"]


class TestAgentServiceSelectBestAgent:
    """Tests for AgentService.select_best_agent_for_task()."""

    @pytest.mark.asyncio
    async def test_select_best_agent_with_task_type(self):
        """Test: select_best_agent_for_task() uses task type when provided."""
        # Arrange
        service = AgentService()
        
        # Act
        result = await service.select_best_agent_for_task(
            "Write some Python code",
            task_type=TaskType.CODE_ANALYSIS
        )
        
        # Assert - should return an agent name (string)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_select_best_agent_without_task_type(self):
        """Test: select_best_agent_for_task() returns default when no task type."""
        # Arrange
        service = AgentService()
        
        # Act
        result = await service.select_best_agent_for_task("Random question")
        
        # Assert
        assert result == service.default_agent


class TestAgentServiceFallback:
    """Tests for AgentService fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_response_finds_alternative(self):
        """Test: _fallback_response() tries alternative agents."""
        # Arrange
        service = AgentService()
        
        mock_agent = Mock()
        mock_agent.generate = AsyncMock(return_value={
            "status": "success",
            "response": "Alternative response"
        })
        
        with patch.object(service.factory, 'get_available_agents', new_callable=AsyncMock) as mock_available:
            mock_available.return_value = {"mistral": False, "llama3": True}
            
            with patch.object(service.factory, 'create_agent', return_value=mock_agent):
                # Act
                result = await service._fallback_response("Hello", "mistral")
        
        # Assert
        assert result["fallback"] is True
        assert result["original_agent"] == "mistral"

    @pytest.mark.asyncio
    async def test_fallback_response_no_agents_available(self):
        """Test: _fallback_response() returns demo mode when no agents."""
        # Arrange
        service = AgentService()
        
        with patch.object(service.factory, 'get_available_agents', new_callable=AsyncMock) as mock_available:
            mock_available.return_value = {"mistral": False, "llama3": False}
            
            # Act
            result = await service._fallback_response("Hello", "mistral")
        
        # Assert
        assert result["status"] == "error"
        assert result["agent_name"] == "mock"
        assert "DEMO MODE" in result["response"]


class TestAgentServiceStatus:
    """Tests for AgentService.get_agent_status()."""

    @pytest.mark.asyncio
    async def test_get_agent_status(self):
        """Test: get_agent_status() returns comprehensive status."""
        # Arrange
        service = AgentService()
        
        with patch.object(service.factory, 'get_available_agents', new_callable=AsyncMock) as mock_available:
            mock_available.return_value = {"mistral": True, "groq": False}
            
            # Act
            status = await service.get_agent_status()
        
        # Assert
        assert "agents" in status
        assert "default_agent" in status
        assert "total_agents" in status
        assert "enabled_agents" in status
        assert "available_agents" in status
        assert status["default_agent"] == "mistral"


class TestAgentServiceMockResponse:
    """Tests for AgentService.generate_mock_response()."""

    @pytest.mark.asyncio
    async def test_generate_mock_response(self):
        """Test: generate_mock_response() returns mock response."""
        # Arrange
        service = AgentService()
        
        # Act
        result = await service.generate_mock_response("Test prompt for mock")
        
        # Assert
        assert result["status"] == "success"
        assert result["agent_name"] == "mock"
        assert "MOCK RESPONSE" in result["response"]
        assert "Test prompt" in result["response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
