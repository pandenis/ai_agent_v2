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
        Generate AI response using Ollama
        
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
        
        # Call Ollama API
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
                
            except httpx.HTTPError as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "response": "I'm having trouble connecting to the AI model. Please try again."
                }
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.ollama_host}/api/tags")
                return response.status_code == 200
            except:
                return False
