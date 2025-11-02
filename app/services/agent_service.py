"""
Agent service for handling AI agent interactions
"""
from typing import List, Dict, Optional
import httpx
from app.core.config import settings
from app.core.security import SecurityValidator


class AgentService:
    """Service for interacting with Ollama-based AI agents"""
    
    def __init__(self):
        self.ollama_host = settings.ollama_host
        self.model = settings.ollama_model
        self.validator = SecurityValidator()
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        """
        Generate AI response using Ollama (with fallback to mock mode)
        
        Args:
            prompt: User's message
            system_prompt: Optional system instructions
            conversation_history: Previous messages for context
            
        Returns:
            Dictionary with response and metadata
        """
        # Validate input
        validated_prompt = self.validator.validate_prompt(prompt)
        
        # Build messages for Ollama
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": validated_prompt
        })
        
        # Try Ollama API
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.ollama_host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "status": "success",
                    "response": result["message"]["content"],
                    "model": self.model,
                    "tokens": result.get("eval_count", 0)
                }
                
            except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
                # Ollama unavailable - use mock mode for demo
                return self._generate_mock_response(validated_prompt, system_prompt)
    
    def _generate_mock_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate a mock response when Ollama is unavailable
        This allows testing the system without a running LLM
        """
        # Extract context from system prompt
        has_documents = system_prompt and "Relevant documents:" in system_prompt
        has_web_search = system_prompt and "Web search results:" in system_prompt
        has_facts = system_prompt and "Known facts about the user:" in system_prompt
        
        # Build intelligent mock response
        response_parts = []
        
        # Acknowledge the question
        if "?" in prompt:
            response_parts.append(f"Regarding your question about '{prompt[:50]}...'")
        else:
            response_parts.append(f"I understand you mentioned: '{prompt[:50]}...'")
        
        # Mention sources if available
        if has_documents:
            response_parts.append("\n\nBased on the documents you provided, I can see relevant information about your topic.")
        
        if has_web_search:
            response_parts.append("\n\nAccording to recent web search results, there is current information available on this subject.")
        
        if has_facts:
            response_parts.append("\n\nI also remember our previous conversations and your preferences.")
        
        # Add demo notice
        response_parts.append("\n\n[DEMO MODE: Ollama not running - this is a mock response demonstrating the multi-source intelligence system. Install and run Ollama to get real AI responses.]")
        
        return {
            "status": "success",
            "response": "".join(response_parts),
            "model": "mock-demo",
            "tokens": 0
        }
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.ollama_host}/api/tags")
                return response.status_code == 200
            except:
                return False
