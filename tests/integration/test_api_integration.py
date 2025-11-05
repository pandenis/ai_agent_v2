"""
Integration tests for API with multi-model support
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_agents_status_endpoint():
    """Test getting agent status"""
    response = client.get("/api/v1/agents/status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "default_agent" in data
    assert "total_agents" in data


def test_agent_selection_endpoint():
    """Test agent selection"""
    response = client.post(
        "/api/v1/agents/select",
        json={
            "prompt": "Write Python code",
            "task_type": "code_analysis"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "selected_agent" in data
    assert "confidence" in data
    assert data["selected_agent"] == "deepseek"


def test_agent_selection_without_task_type():
    """Test agent selection without explicit task type"""
    response = client.post(
        "/api/v1/agents/select",
        json={"prompt": "Hello, how are you?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "selected_agent" in data


def test_agent_selection_invalid_task_type():
    """Test agent selection with invalid task type"""
    response = client.post(
        "/api/v1/agents/select",
        json={
            "prompt": "Test",
            "task_type": "invalid_type"
        }
    )
    assert response.status_code == 400


def test_openapi_docs():
    """Test that OpenAPI docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
