import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.modelfile_service import ModelfileService, ModelNotFoundError


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


@pytest.mark.asyncio
async def test_get_model_returns_model_info_with_modelfile():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "modelfile": "FROM mistral\nSYSTEM \"You are an assistant\"",
        "details": {},
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().get_model("mistral")

    assert isinstance(result, dict)
    assert result["modelfile"].startswith("FROM mistral")


@pytest.mark.asyncio
async def test_get_model_raises_model_not_found_error_for_unknown_model():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ModelNotFoundError):
            await ModelfileService().get_model("nonexistent-model")
