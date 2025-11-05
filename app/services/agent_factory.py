"""
Agent factory for creating and managing AI agents
"""
from typing import Dict, Optional, Callable
import httpx
from app.core.agent_config import (
    AgentConfig,
    AgentType,
    OllamaAgentConfig,
    CloudAgentConfig,
    LlamaCppAgentConfig,
    agent_registry
)
from app.core.config import settings


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.enabled = config.enabled
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Generate response from agent"""
        raise NotImplementedError("Subclasses must implement generate()")
    
    async def health_check(self) -> bool:
        """Check if agent is available and healthy"""
        raise NotImplementedError("Subclasses must implement health_check()")


class OllamaAgent(BaseAgent):
    """Agent using Ollama API"""
    
    def __init__(self, config: OllamaAgentConfig):
        super().__init__(config)
        self.base_url = config.base_url
        self.model_name = config.model_name
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Generate response using Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens
                    }
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "response": result["message"]["content"],
                "model": self.model_name,
                "tokens": result.get("eval_count", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response": f"Error from {self.name}: {str(e)}"
            }
    
    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check Ollama is running
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            return any(self.model_name in name for name in model_names)
            
        except Exception:
            return False


class CloudAgent(BaseAgent):
    """Agent using cloud API (Groq, OpenAI, etc)"""
    
    def __init__(self, config: CloudAgentConfig):
        super().__init__(config)
        self.api_base_url = config.api_base_url
        self.api_key = config.api_key or settings.groq_api_key
        self.model_id = config.model_id
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Generate response using cloud API"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "API key not configured",
                "response": f"{self.name} requires API key"
            }
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.post(
                f"{self.api_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "temperature": temperature or self.config.temperature,
                    "max_tokens": max_tokens or self.config.max_tokens
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "response": result["choices"][0]["message"]["content"],
                "model": self.model_id,
                "tokens": result.get("usage", {}).get("total_tokens", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response": f"Error from {self.name}: {str(e)}"
            }
    
    async def health_check(self) -> bool:
        """Check if cloud API is accessible"""
        if not self.api_key:
            return False
        
        try:
            response = await self.client.get(
                f"{self.api_base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False


class AgentFactory:
    """Factory for creating agent instances"""
    
    def __init__(self):
        self._agent_cache: Dict[str, BaseAgent] = {}
    
    def create_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Create or retrieve cached agent instance"""
        # Check cache first
        if agent_name.lower() in self._agent_cache:
            return self._agent_cache[agent_name.lower()]
        
        # Get config from registry
        config = agent_registry.get_agent_config(agent_name)
        if not config:
            return None
        
        if not config.enabled:
            return None
        
        # Create appropriate agent based on type
        agent = None
        
        if config.agent_type == AgentType.LOCAL_OLLAMA:
            agent = OllamaAgent(config)
        elif config.agent_type == AgentType.CLOUD_API:
            agent = CloudAgent(config)
        elif config.agent_type == AgentType.LOCAL_LLAMA_CPP:
            # TODO: Implement LlamaCppAgent
            return None
        
        # Cache the agent
        if agent:
            self._agent_cache[agent_name.lower()] = agent
        
        return agent
    
    async def get_available_agents(self) -> Dict[str, bool]:
        """Get health status of all agents"""
        status = {}
        
        for agent_name in agent_registry.list_agents(enabled_only=True):
            agent = self.create_agent(agent_name)
            if agent:
                status[agent_name] = await agent.health_check()
            else:
                status[agent_name] = False
        
        return status
    
    def clear_cache(self):
        """Clear agent cache (useful for testing)"""
        self._agent_cache.clear()


# Global factory instance
agent_factory = AgentFactory()
