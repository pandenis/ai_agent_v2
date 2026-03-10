"""E2E tests for Modelfile endpoints — requires Ollama running"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_models_returns_real_models_from_ollama():
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert "models" in response.json()
    assert isinstance(response.json()["models"], list)
