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


@pytest.mark.asyncio
async def test_create_model_sends_modelfile_to_ollama():
    modelfile = "FROM llama3.1\nSYSTEM \"You are a medical assistant\""

    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().create_model("medical-ai", modelfile)

    assert isinstance(result, dict)
    assert result["success"] == True
    mock_client.post.assert_called_once_with(
        "http://localhost:11434/api/create",
        json={"name": "medical-ai", "modelfile": modelfile, "stream": False},
    )


@pytest.mark.asyncio
async def test_create_model_returns_error_dict_on_ollama_failure():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().create_model("bad-model", "FROM nonexistent")

    assert isinstance(result, dict)
    assert result["success"] == False
    assert isinstance(result["error"], str) and result["error"]


@pytest.mark.asyncio
async def test_delete_model_returns_true_on_success():
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await ModelfileService().delete_model("medical-ai")

    assert result is True
    mock_client.request.assert_called_once_with(
        "DELETE", "http://localhost:11434/api/delete", json={"name": "medical-ai"}
    )
