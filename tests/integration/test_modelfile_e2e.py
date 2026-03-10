"""E2E tests for Modelfile endpoints — requires Ollama running"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_models_returns_real_models_from_ollama():
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert "models" in response.json()
    assert isinstance(response.json()["models"], list)


def test_post_models_creates_real_model_and_appears_in_list():
    response = client.post(
        "/api/v1/models",
        json={"name": "test-agent", "modelfile": "FROM mistral\nSYSTEM \"You are a test agent.\""},
    )

    assert response.status_code == 201
    assert response.json()["success"] == True

    response = client.get("/api/v1/models")
    names = [m["name"] for m in response.json()["models"]]
    assert any(n == "test-agent" or n.startswith("test-agent:") for n in names)
