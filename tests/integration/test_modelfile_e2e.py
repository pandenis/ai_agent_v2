"""E2E tests for Modelfile endpoints — requires Ollama running"""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

IN_CI = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"

client = TestClient(app)


def test_get_models_returns_real_models_from_ollama():
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert "models" in response.json()
    assert isinstance(response.json()["models"], list)


@pytest.mark.skipif(IN_CI, reason="Requires Ollama running locally")
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


@pytest.mark.skipif(IN_CI, reason="Requires Ollama running locally")
def test_delete_model_removes_real_model_from_ollama():
    response = client.delete("/api/v1/models/test-agent:latest")

    assert response.status_code == 204

    response = client.get("/api/v1/models")
    assert "test-agent:latest" not in [m["name"] for m in response.json()["models"]]
