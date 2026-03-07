import logging

import httpx

logger = logging.getLogger(__name__)


class ModelNotFoundError(Exception):
    pass


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

    async def get_model(self, name: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.ollama_url}/api/show", json={"name": name})
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ModelNotFoundError(name)
                raise
            return response.json()

    async def create_model(self, name: str, modelfile: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/create",
                json={"name": name, "modelfile": modelfile, "stream": False},
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                return {"success": False, "name": name, "output": "", "error": str(e)}
            return {"success": True, "name": name, "output": response.json().get("status", "")}

    async def delete_model(self, name: str) -> bool:
        async with httpx.AsyncClient() as client:
            await client.request("DELETE", f"{self.ollama_url}/api/delete", json={"name": name})
            return True
