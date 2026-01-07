"""
Tests for enhanced agent service with multi-model support
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agent_config import TaskType
from app.services.agent_service import AgentService


@pytest.fixture
def agent_service():
    """Create agent service instance"""
    return AgentService()


@pytest.mark.asyncio
async def test_generate_response_default_agent(agent_service):
    """Test generating response with default agent"""
    with patch.object(agent_service.factory, "create_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.health_check = AsyncMock(return_value=True)
        mock_agent.generate = AsyncMock(return_value={"status": "success", "response": "Hello!", "model": "mistral"})
        mock_agent.config = MagicMock()
        mock_agent.config.agent_type.value = "local_ollama"
        mock_agent.config.capabilities = []

        mock_create.return_value = mock_agent

        result = await agent_service.generate_response("Hi")

        assert result["status"] == "success"
        assert result["response"] == "Hello!"
        assert "agent_name" in result


@pytest.mark.asyncio
async def test_generate_response_specific_agent(agent_service):
    """Test generating response with specific agent"""
    with patch.object(agent_service.factory, "create_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.health_check = AsyncMock(return_value=True)
        mock_agent.generate = AsyncMock(return_value={"status": "success", "response": "Code response", "model": "deepseek"})
        mock_agent.config = MagicMock()
        mock_agent.config.agent_type.value = "local_llama_cpp"
        mock_agent.config.capabilities = []

        mock_create.return_value = mock_agent

        result = await agent_service.generate_response("Write Python code", agent_name="deepseek")

        assert result["status"] == "success"
        assert result["agent_name"] == "deepseek"


@pytest.mark.asyncio
async def test_select_best_agent_for_task(agent_service):
    """Test automatic agent selection"""
    # Test code task
    best = await agent_service.select_best_agent_for_task("Write Python code", task_type=TaskType.CODE_ANALYSIS)
    assert best == "deepseek"

    # Test medical task
    best = await agent_service.select_best_agent_for_task("Medical question", task_type=TaskType.MEDICAL_QUERY)
    assert best == "medical"


@pytest.mark.asyncio
async def test_fallback_when_agent_unavailable(agent_service):
    """Test fallback to alternative agent"""
    with patch.object(agent_service.factory, "create_agent") as mock_create:
        # First call returns None (agent unavailable)
        mock_create.return_value = None

        with patch.object(agent_service.factory, "get_available_agents") as mock_available:
            mock_available.return_value = {}

            result = await agent_service.generate_response("Hi")

            assert result["status"] == "error"
            assert "fallback" in result
            assert "DEMO MODE" in result["response"]


@pytest.mark.asyncio
async def test_get_agent_status(agent_service):
    """Test getting status of all agents"""
    with patch.object(agent_service.factory, "get_available_agents") as mock_available:
        mock_available.return_value = {"mistral": True, "llama3": True, "groq": False, "deepseek": False, "medical": False}

        status = await agent_service.get_agent_status()

        assert "agents" in status
        assert "default_agent" in status
        assert status["default_agent"] == "mistral"
        assert status["available_agents"] == 2
        assert len(status["agents"]) >= 5


@pytest.mark.asyncio
async def test_generate_mock_response(agent_service):
    """Test mock response generation"""
    result = await agent_service.generate_mock_response("Test prompt")

    assert result["status"] == "success"
    assert "MOCK RESPONSE" in result["response"]
    assert result["agent_name"] == "mock"


@pytest.mark.asyncio
async def test_unhealthy_agent_fallback(agent_service):
    """Test fallback when agent health check fails"""
    with patch.object(agent_service.factory, "create_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.health_check = AsyncMock(return_value=False)  # Unhealthy
        mock_create.return_value = mock_agent

        with patch.object(agent_service.factory, "get_available_agents") as mock_available:
            mock_available.return_value = {}

            result = await agent_service.generate_response("Hi")

            assert "fallback" in result
            assert "health check failed" in result.get("fallback_reason", "")


@pytest.mark.asyncio
async def test_select_best_agent_returns_found_agent(agent_service):
    """Test: select_best_agent_for_task returns agent when found"""
    # Act - GENERAL_CHAT should find an agent
    result = await agent_service.select_best_agent_for_task(
        prompt="Hello, how are you?",
        task_type=TaskType.GENERAL_CHAT
    )
    
    # Assert - should return best agent for general chat (groq has 0.95)
    assert result is not None
    assert result in ["groq", "mistral", "llama3"]  # Any of these could be best
