"""
Tests for agent registry and configuration
"""
import pytest
from app.core.agent_config import (
    AgentRegistry,
    TaskType,
    AgentCapability,
    OllamaAgentConfig
)


def test_agent_registry_initialization():
    """Test that registry initializes with default agents"""
    registry = AgentRegistry()
    agents = registry.list_agents(enabled_only=False)
    
    assert "mistral" in agents
    assert "llama3" in agents
    assert "groq" in agents
    assert "deepseek" in agents
    assert "medical" in agents


def test_get_agent_config():
    """Test retrieving agent configuration"""
    registry = AgentRegistry()
    
    config = registry.get_agent_config("mistral")
    assert config is not None
    assert config.name == "Mistral"
    assert config.max_tokens > 0


def test_find_best_agent_for_task():
    """Test finding best agent for specific tasks"""
    registry = AgentRegistry()
    
    # Code tasks should prefer DeepSeek
    best = registry.find_best_agent_for_task(TaskType.CODE_ANALYSIS)
    assert best == "deepseek"
    
    # Medical tasks should prefer Medical AI
    best = registry.find_best_agent_for_task(TaskType.MEDICAL_QUERY)
    assert best == "medical"


def test_capability_scoring():
    """Test capability scoring system"""
    registry = AgentRegistry()
    config = registry.get_agent_config("mistral")
    
    # Should have high score for general chat
    score = config.get_capability_score(TaskType.GENERAL_CHAT)
    assert score >= 0.8
    
    # Should have low/zero score for medical
    score = config.get_capability_score(TaskType.MEDICAL_QUERY)
    assert score < 0.5


def test_register_custom_agent():
    """Test registering a custom agent"""
    registry = AgentRegistry()
    
    custom_config = OllamaAgentConfig(
        name="CustomAgent",
        description="Test agent",
        model_name="custom-model",
        capabilities=[
            AgentCapability("general_chat", 0.5, "Basic chat")
        ]
    )
    
    registry.register_agent(custom_config)
    
    assert "customagent" in registry.list_agents(enabled_only=False)
    config = registry.get_agent_config("customagent")
    assert config.name == "CustomAgent"


def test_enable_disable_agent():
    """Test enabling and disabling agents"""
    registry = AgentRegistry()
    
    # Disable agent
    registry.disable_agent("mistral")
    agents = registry.list_agents(enabled_only=True)
    assert "mistral" not in agents
    
    # Enable agent
    registry.enable_agent("mistral")
    agents = registry.list_agents(enabled_only=True)
    assert "mistral" in agents
