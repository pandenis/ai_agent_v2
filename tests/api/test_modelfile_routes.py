from unittest.mock import AsyncMock, patch

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
