"""
Enhanced Agent Service with multi-model support via AgentFactory
"""
from typing import Optional, Dict, Any

# Security import
from security.input_validation import validate_input

from app.core.config import settings
from app.services.agent_factory import agent_factory
from app.core.agent_config import agent_registry, TaskType


class AgentService:
    """
    Service for interacting with AI agents
    Now supports multiple models via AgentFactory
    """
    
    def __init__(self):
        self.factory = agent_factory
        self.default_agent = "mistral"  # Fallback agent
    
    async def generate_response(
        self,
        prompt: str,
        agent_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate response from specified agent (or default)
        
        Args:
            prompt: User prompt
            agent_name: Specific agent to use (optional)
            system_prompt: System prompt (optional)
            temperature: Override temperature (optional)
            max_tokens: Override max tokens (optional)
            
        Returns:
            Dict with response, status, and metadata
        """
        # Security: Validate user prompt
        is_valid, sanitized_prompt, error = validate_input(prompt)
        if not is_valid:
            return {
                "response": f"Invalid input: {error}",
                "status": "error",
                "agent": "security_validator",
                "error": error
            }

        # Use sanitized prompt
        prompt = sanitized_prompt

        # Use specified agent or default
        agent_name = agent_name or self.default_agent
        
        # Create/get agent
        agent = self.factory.create_agent(agent_name)
        
        if not agent:
            # Agent not available, try fallback
            return await self._fallback_response(prompt, agent_name)
        
        # Check if agent is healthy
        is_healthy = await agent.health_check()
        if not is_healthy:
            return await self._fallback_response(
                prompt, 
                agent_name,
                reason="Agent health check failed"
            )
        
        # Generate response
        result = await agent.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Add agent metadata
        result["agent_name"] = agent_name
        result["agent_config"] = {
            "type": agent.config.agent_type.value,
            "capabilities": [c.name for c in agent.config.capabilities]
        }
        
        return result
    
    async def select_best_agent_for_task(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None
    ) -> str:
        """
        Automatically select the best agent for a task
        
        Args:
            prompt: User prompt (for future ML-based selection)
            task_type: Explicit task type (optional)
            
        Returns:
            Name of best agent for the task
        """
        if task_type:
            best_agent = agent_registry.find_best_agent_for_task(task_type)
            if best_agent:
                return best_agent
        
        # TODO: In future, use ML to classify task type from prompt
        # For now, return default
        return self.default_agent
    
    async def _fallback_response(
        self,
        prompt: str,
        failed_agent: str,
        reason: str = "Agent not available"
    ) -> Dict[str, Any]:
        """
        Provide fallback response when agent fails
        """
        # Try to find alternative agent
        available_agents = await self.factory.get_available_agents()
        
        for agent_name, is_available in available_agents.items():
            if is_available and agent_name != failed_agent:
                # Try this agent
                agent = self.factory.create_agent(agent_name)
                if agent:
                    result = await agent.generate(prompt)
                    result["fallback"] = True
                    result["original_agent"] = failed_agent
                    result["fallback_reason"] = reason
                    return result
        
        # No agents available - return mock response
        return {
            "status": "error",
            "response": f"[DEMO MODE: No AI agents available. {reason}]\n\nTo enable AI responses:\n1. Install Ollama: https://ollama.ai\n2. Run: ollama pull mistral\n3. Start server: ollama serve",
            "agent_name": "mock",
            "fallback": True,
            "original_agent": failed_agent,
            "fallback_reason": reason
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all configured agents
        
        Returns:
            Dict with agent availability and configuration
        """
        available = await self.factory.get_available_agents()
        
        status = {
            "agents": {},
            "default_agent": self.default_agent,
            "total_agents": len(agent_registry.list_agents(enabled_only=False)),
            "enabled_agents": len(agent_registry.list_agents(enabled_only=True)),
            "available_agents": sum(1 for v in available.values() if v)
        }
        
        for agent_name in agent_registry.list_agents(enabled_only=False):
            config = agent_registry.get_agent_config(agent_name)
            status["agents"][agent_name] = {
                "enabled": config.enabled,
                "available": available.get(agent_name, False),
                "type": config.agent_type.value,
                "description": config.description,
                "capabilities": [
                    {"name": c.name, "confidence": c.confidence}
                    for c in config.capabilities
                ]
            }
        
        return status
    
    async def generate_mock_response(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a mock response (for testing without models)
        """
        return {
            "status": "success",
            "response": f"[MOCK RESPONSE] You asked: {prompt[:100]}...",
            "agent_name": "mock",
            "model": "mock",
            "tokens": 0
        }
