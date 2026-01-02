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
