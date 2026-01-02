"""
Tests for AgentFactory and Agent classes.

This module tests:
- BaseAgent abstract methods
- OllamaAgent generation and health checks
- CloudAgent generation and health checks
- AgentFactory agent creation and caching
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

from app.services.agent_factory import (
    BaseAgent,
    OllamaAgent,
    CloudAgent,
    AgentFactory,
    agent_factory,
)
from app.core.agent_config import (
    AgentConfig,
    AgentType,
    OllamaAgentConfig,
    CloudAgentConfig,
    AgentCapability,
    TaskType,
)


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    @pytest.mark.asyncio
    async def test_generate_raises_not_implemented(self):
        """Test: BaseAgent.generate() raises NotImplementedError."""
        # Arrange
        mock_config = Mock(spec=AgentConfig)
        mock_config.name = "test_agent"
        mock_config.enabled = True
        agent = BaseAgent(mock_config)
        
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Subclasses must implement generate"):
            await agent.generate("test prompt")

    @pytest.mark.asyncio
    async def test_health_check_raises_not_implemented(self):
        """Test: BaseAgent.health_check() raises NotImplementedError."""
        # Arrange
        mock_config = Mock(spec=AgentConfig)
        mock_config.name = "test_agent"
        mock_config.enabled = True
        agent = BaseAgent(mock_config)
        
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Subclasses must implement health_check"):
            await agent.health_check()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestOllamaAgent:
    """Tests for OllamaAgent class."""

    def _create_ollama_config(self) -> OllamaAgentConfig:
        """Helper to create test OllamaAgentConfig."""
        return OllamaAgentConfig(
            name="TestOllama",
            description="Test Ollama agent",
            capabilities=[
                AgentCapability("general_chat", 0.9, "Test capability")
            ],
            base_url="http://localhost:11434",
            model_name="test-model",
            max_tokens=100,
            temperature=0.5,
        )

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test: OllamaAgent.generate() returns success response."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Hello, test response!"},
            "eval_count": 10
        }
        
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # Act
            result = await agent.generate("Hello, world!")
        
        # Assert
        assert result["status"] == "success"
        assert result["response"] == "Hello, test response!"
        assert result["model"] == "test-model"
        assert result["tokens"] == 10

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test: OllamaAgent.generate() includes system prompt in messages."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Response with system prompt"},
            "eval_count": 5
        }
        
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # Act
            result = await agent.generate(
                "User message",
                system_prompt="You are a helpful assistant"
            )
        
        # Assert
        assert result["status"] == "success"
        # Verify system prompt was included in the call
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_generate_exception_returns_error(self):
        """Test: OllamaAgent.generate() handles exceptions gracefully."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            # Act
            result = await agent.generate("Hello")
        
        # Assert
        assert result["status"] == "error"
        assert "error" in result
        assert "Connection refused" in result["error"] or "Connection" in result["response"]
