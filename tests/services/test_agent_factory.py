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

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test: OllamaAgent.health_check() returns True when model available."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "test-model:latest"},
                {"name": "other-model:7b"}
            ]
        }
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        """Test: OllamaAgent.health_check() returns False when model not available."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model:7b"}
            ]
        }
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_server_error(self):
        """Test: OllamaAgent.health_check() returns False on server error."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self):
        """Test: OllamaAgent.health_check() returns False on connection error."""
        # Arrange
        config = self._create_ollama_config()
        agent = OllamaAgent(config)
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is False


class TestCloudAgent:
    """Tests for CloudAgent class."""

    def _create_cloud_config(self, api_key: str = "test-api-key") -> CloudAgentConfig:
        """Helper to create test CloudAgentConfig."""
        return CloudAgentConfig(
            name="TestCloud",
            description="Test Cloud agent",
            capabilities=[
                AgentCapability("general_chat", 0.95, "Test capability")
            ],
            api_base_url="https://api.test.com/v1",
            api_key=api_key,
            model_id="test-model-id",
            max_tokens=200,
            temperature=0.7,
        )

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test: CloudAgent.generate() returns success response."""
        # Arrange
        config = self._create_cloud_config()
        agent = CloudAgent(config)
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Cloud response!"}}],
            "usage": {"total_tokens": 25}
        }
        
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # Act
            result = await agent.generate("Hello from cloud!")
        
        # Assert
        assert result["status"] == "success"
        assert result["response"] == "Cloud response!"
        assert result["model"] == "test-model-id"
        assert result["tokens"] == 25

    @pytest.mark.asyncio
    async def test_generate_no_api_key_returns_error(self):
        """Test: CloudAgent.generate() returns error when no API key."""
        # Arrange
        config = self._create_cloud_config(api_key="")
        agent = CloudAgent(config)
        # Ensure api_key is empty (settings might override)
        agent.api_key = ""
        
        # Act
        result = await agent.generate("Hello")
        
        # Assert
        assert result["status"] == "error"
        assert "API key" in result["error"] or "API key" in result["response"]

    @pytest.mark.asyncio
    async def test_generate_exception_returns_error(self):
        """Test: CloudAgent.generate() handles exceptions gracefully."""
        # Arrange
        config = self._create_cloud_config()
        agent = CloudAgent(config)
        
        with patch.object(agent.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Rate limited", 
                request=Mock(), 
                response=Mock(status_code=429)
            )
            
            # Act
            result = await agent.generate("Hello")
        
        # Assert
        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test: CloudAgent.health_check() returns True when API accessible."""
        # Arrange
        config = self._create_cloud_config()
        agent = CloudAgent(config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self):
        """Test: CloudAgent.health_check() returns False when no API key."""
        # Arrange
        config = self._create_cloud_config(api_key="")
        agent = CloudAgent(config)
        agent.api_key = ""
        
        # Act
        result = await agent.health_check()
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self):
        """Test: CloudAgent.health_check() returns False on API error."""
        # Arrange
        config = self._create_cloud_config()
        agent = CloudAgent(config)
        
        with patch.object(agent.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("API unavailable")
            
            # Act
            result = await agent.health_check()
        
        # Assert
        assert result is False


class TestAgentFactory:
    """Tests for AgentFactory class."""

    def setup_method(self):
        """Clear cache before each test."""
        agent_factory.clear_cache()

    def test_create_agent_ollama_type(self):
        """Test: AgentFactory creates OllamaAgent for LOCAL_OLLAMA type."""
        # Arrange
        factory = AgentFactory()
        
        # Act - 'mistral' is configured as LOCAL_OLLAMA in agent_registry
        agent = factory.create_agent("mistral")
        
        # Assert
        assert agent is not None
        assert isinstance(agent, OllamaAgent)
        assert agent.name == "Mistral"

    def test_create_agent_cloud_type(self):
        """Test: AgentFactory creates CloudAgent for CLOUD_API type."""
        # Arrange
        factory = AgentFactory()
        
        # Act - 'groq' is configured as CLOUD_API in agent_registry
        agent = factory.create_agent("groq")
        
        # Assert
        assert agent is not None
        assert isinstance(agent, CloudAgent)
        assert agent.name == "Groq"

    def test_create_agent_caches_instance(self):
        """Test: AgentFactory caches agent instances."""
        # Arrange
        factory = AgentFactory()
        
        # Act
        agent1 = factory.create_agent("mistral")
        agent2 = factory.create_agent("mistral")
        
        # Assert - same instance returned
        assert agent1 is agent2

    def test_create_agent_unknown_returns_none(self):
        """Test: AgentFactory returns None for unknown agent."""
        # Arrange
        factory = AgentFactory()
        
        # Act
        agent = factory.create_agent("nonexistent_agent")
        
        # Assert
        assert agent is None

    def test_create_agent_disabled_returns_none(self):
        """Test: AgentFactory returns None for disabled agent."""
        # Arrange
        factory = AgentFactory()
        
        # Temporarily disable an agent
        from app.core.agent_config import agent_registry
        original_enabled = agent_registry.get_agent_config("mistral").enabled
        agent_registry.disable_agent("mistral")
        
        try:
            # Act
            agent = factory.create_agent("mistral")
            
            # Assert
            assert agent is None
        finally:
            # Restore original state
            if original_enabled:
                agent_registry.enable_agent("mistral")

    def test_clear_cache(self):
        """Test: AgentFactory.clear_cache() clears cached agents."""
        # Arrange
        factory = AgentFactory()
        agent1 = factory.create_agent("mistral")
        
        # Act
        factory.clear_cache()
        agent2 = factory.create_agent("mistral")
        
        # Assert - different instances after cache clear
        assert agent1 is not agent2

    @pytest.mark.asyncio
    async def test_get_available_agents(self):
        """Test: AgentFactory.get_available_agents() returns health status."""
        # Arrange
        factory = AgentFactory()
        
        # Act
        with patch.object(OllamaAgent, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            available = await factory.get_available_agents()
        
        # Assert
        assert isinstance(available, dict)
        # Should have at least some agents
        assert len(available) > 0
