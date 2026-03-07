import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.modelfile_service import ModelfileService


@pytest.mark.asyncio
async def test_list_models_returns_list_of_models():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "mistral:latest"},
            {"name": "llama3.1:latest"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().list_models()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "mistral:latest"


@pytest.mark.asyncio
async def test_list_models_returns_empty_list_when_ollama_unavailable():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().list_models()

    assert result == []
