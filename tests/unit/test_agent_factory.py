"""
Tests for agent factory
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agent_config import agent_registry
from app.services.agent_factory import AgentFactory, CloudAgent, OllamaAgent


def test_agent_factory_initialization():
    """Test factory initializes correctly"""
    factory = AgentFactory()
    assert factory._agent_cache == {}


def test_create_ollama_agent():
    """Test creating Ollama agent"""
    factory = AgentFactory()
    agent = factory.create_agent("mistral")

    assert agent is not None
    assert isinstance(agent, OllamaAgent)
    assert agent.name == "Mistral"


def test_create_cloud_agent():
    """Test creating cloud agent"""
    factory = AgentFactory()
    agent = factory.create_agent("groq")

    assert agent is not None
    assert isinstance(agent, CloudAgent)
    assert agent.name == "Groq"


def test_agent_caching():
    """Test that agents are cached"""
    factory = AgentFactory()

    agent1 = factory.create_agent("mistral")
    agent2 = factory.create_agent("mistral")

    assert agent1 is agent2  # Same instance


def test_create_disabled_agent():
    """Test creating disabled agent returns None"""
    factory = AgentFactory()

    # Disable agent
    agent_registry.disable_agent("mistral")

    agent = factory.create_agent("mistral")
    assert agent is None

    # Re-enable for other tests
    agent_registry.enable_agent("mistral")


def test_create_nonexistent_agent():
    """Test creating non-existent agent returns None"""
    factory = AgentFactory()
    agent = factory.create_agent("nonexistent")

    assert agent is None


@pytest.mark.asyncio
async def test_ollama_agent_health_check():
    """Test Ollama agent health check"""
    factory = AgentFactory()
    agent = factory.create_agent("mistral")

    # Mock httpx client
    with patch.object(agent.client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "mistral:7b-instruct"}]}
        mock_get.return_value = mock_response

        is_healthy = await agent.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_ollama_agent_generate():
    """Test Ollama agent generation"""
    factory = AgentFactory()
    agent = factory.create_agent("mistral")

    # Mock httpx client
    with patch.object(agent.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "Hello!"}, "eval_count": 10}
        mock_post.return_value = mock_response

        result = await agent.generate("Hi")

        assert result["status"] == "success"
        assert result["response"] == "Hello!"
        assert result["tokens"] == 10


def test_clear_cache():
    """Test clearing agent cache"""
    factory = AgentFactory()

    # Create agent (adds to cache)
    factory.create_agent("mistral")
    assert len(factory._agent_cache) > 0

    # Clear cache
    factory.clear_cache()
    assert factory._agent_cache == {}


def test_create_llamacpp_agent_returns_none():
    """Test: LlamaCpp agent type returns None (not implemented yet)"""
    # Arrange
    factory = AgentFactory()
    
    # Act - deepseek is configured as LOCAL_LLAMA_CPP type
    agent = factory.create_agent("deepseek")
    
    # Assert - should return None because LlamaCpp not implemented
    assert agent is None
    # Should NOT be cached when None
    assert "deepseek" not in factory._agent_cache


@pytest.mark.asyncio
async def test_cloud_agent_generate_with_system_prompt():
    """Test: CloudAgent.generate() includes system_prompt in messages"""
    # Arrange
    factory = AgentFactory()
    agent = factory.create_agent("groq")
    
    # Set API key (required for generate to proceed)
    agent.api_key = "test-api-key"
    
    # Mock the HTTP client
    with patch.object(agent.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}]
        }
        mock_post.return_value = mock_response
        
        # Act - call with system_prompt
        result = await agent.generate(
            prompt="Hello",
            system_prompt="You are a helpful assistant"
        )
        
        # Assert - verify system_prompt was included
        call_args = mock_post.call_args
        json_data = call_args.kwargs.get("json") or call_args[1].get("json")
        messages = json_data["messages"]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"


def test_create_agent_unknown_type_returns_none():
    """Test: Unknown agent type returns None and is not cached"""
    from unittest.mock import Mock
    from app.core.agent_config import AgentType
    
    factory = AgentFactory()
    
    # Mock config with unknown type (not OLLAMA, CLOUD, or LLAMA_CPP)
    mock_config = Mock()
    mock_config.enabled = True
    mock_config.agent_type = Mock()  # Unknown type - won't match any
    mock_config.agent_type.value = "unknown_type"
    
    with patch.object(agent_registry, "get_agent_config", return_value=mock_config):
        # Act
        agent = factory.create_agent("fake_agent")
        
        # Assert - should return None
        assert agent is None
        # Should NOT be cached
        assert "fake_agent" not in factory._agent_cache
