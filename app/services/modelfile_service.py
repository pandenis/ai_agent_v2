import logging

import httpx

logger = logging.getLogger(__name__)


class ModelfileService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"

    async def list_models(self) -> list:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.json()["models"]
        except Exception as e:
            logger.warning("Ollama unavailable: %s", e)
            return []
