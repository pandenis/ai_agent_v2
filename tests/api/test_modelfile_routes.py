from unittest.mock import AsyncMock, patch

from app.services.modelfile_service import ModelNotFoundError

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_models_returns_200_with_list():
    mock_models = [{"name": "mistral:latest"}, {"name": "llama3.1:latest"}]

    with patch(
        "app.services.modelfile_service.ModelfileService.list_models",
        new=AsyncMock(return_value=mock_models),
    ):
        response = client.get("/api/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) == 2
    assert data["models"][0]["name"] == "mistral:latest"


def test_get_models_returns_empty_list_when_ollama_unavailable():
    with patch(
        "app.services.modelfile_service.ModelfileService.list_models",
        new=AsyncMock(return_value=[]),
    ):
        response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json()["models"] == []


def test_get_model_by_name_returns_200_with_modelfile():
    mock_detail = {
        "name": "mistral",
        "modelfile": "FROM mistral\nSYSTEM \"You are an assistant\"",
    }

    with patch(
        "app.services.modelfile_service.ModelfileService.get_model",
        new=AsyncMock(return_value=mock_detail),
    ):
        response = client.get("/api/v1/models/mistral")

    assert response.status_code == 200
    assert response.json()["name"] == "mistral"
    assert response.json()["modelfile"].startswith("FROM mistral")


def test_get_model_by_name_returns_404_for_unknown_model():
    with patch(
        "app.services.modelfile_service.ModelfileService.get_model",
        new=AsyncMock(side_effect=ModelNotFoundError("nonexistent")),
    ):
        response = client.get("/api/v1/models/nonexistent")

    assert response.status_code == 404
    assert "nonexistent" in response.json()["detail"]


def test_post_models_creates_model_and_returns_201():
    with patch(
        "app.services.modelfile_service.ModelfileService.create_model",
        new=AsyncMock(return_value={"success": True, "name": "medical-ai", "output": "success"}),
    ):
        response = client.post(
            "/api/v1/models",
            json={"name": "medical-ai", "modelfile": "FROM llama3.1\nSYSTEM \"You are a medical assistant\""},
        )

    assert response.status_code == 201
    assert response.json()["success"] == True
    assert response.json()["name"] == "medical-ai"


def test_post_models_returns_422_when_name_missing():
    response = client.post("/api/v1/models", json={})
    assert response.status_code == 422


def test_post_models_returns_422_when_modelfile_missing():
    response = client.post("/api/v1/models", json={"name": "medical-ai"})
    assert response.status_code == 422
