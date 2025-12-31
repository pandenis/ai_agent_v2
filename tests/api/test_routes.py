"""
Tests for API routes.

Covers all endpoints in app/api/routes.py
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_returns_healthy(self):
        """Test: GET /health returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestAgentsEndpoints:
    """Tests for /agents/* endpoints."""

    def test_get_agents_status_returns_200(self):
        """Test: GET /agents/status returns agent statuses."""
        response = client.get("/api/v1/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data or "status" in data

    def test_select_agent_success(self):
        """Test: POST /agents/select returns selected agent."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": "What is the weather today?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data

    def test_select_agent_invalid_input_returns_400(self):
        """Test: POST /agents/select with invalid input returns 400."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": ""}  # Empty prompt
        )

        assert response.status_code == 400

    def test_select_agent_invalid_task_type_returns_400(self):
        """Test: POST /agents/select with invalid task_type returns 400."""
        response = client.post(
            "/api/v1/agents/select",
            json={"prompt": "Hello world", "task_type": "invalid_type"}
        )

        assert response.status_code == 400
        assert "Invalid task_type" in response.json()["detail"]

class TestSessionEndpoints:
    """Tests for /sessions/* endpoints."""

    def test_create_session_success(self):
        """Test: POST /sessions creates new session."""
        response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["agent_name"] == "mistral"

    def test_get_sessions_returns_list(self):
        """Test: GET /sessions returns list of sessions."""
        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_session_not_found_returns_404(self):
        """Test: GET /sessions/{id} with invalid id returns 404."""
        response = client.get("/api/v1/sessions/nonexistent-session-id")

        assert response.status_code == 404

    def test_get_session_success(self):
        """Test: GET /sessions/{id} returns session details."""
        # First create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "test-agent"}
        )
        session_id = create_response.json()["session_id"]

        # Then get it
        response = client.get(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    def test_get_session_messages_not_found_returns_404(self):
        """Test: GET /sessions/{id}/messages with invalid session returns 404."""
        response = client.get("/api/v1/sessions/nonexistent-id/messages")

        assert response.status_code == 404

    def test_get_session_messages_success(self):
        """Test: GET /sessions/{id}/messages returns messages list."""
        # First create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "test-agent"}
        )
        session_id = create_response.json()["session_id"]

        # Get messages (empty but valid)
        response = client.get(f"/api/v1/sessions/{session_id}/messages")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_session_facts_not_found_returns_404(self):
        """Test: GET /sessions/{id}/facts with invalid session returns 404."""
        response = client.get("/api/v1/sessions/nonexistent-id/facts")

        assert response.status_code == 404

    def test_get_session_facts_success(self):
        """Test: GET /sessions/{id}/facts returns facts list."""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "test-agent"}
        )
        session_id = create_response.json()["session_id"]

        # Get facts (empty but valid)
        response = client.get(f"/api/v1/sessions/{session_id}/facts")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "facts" in data

class TestMemoryEndpoints:
    """Tests for /memory/* endpoints."""

    def test_get_facts_returns_list(self):
        """Test: GET /memory/facts returns facts list."""
        response = client.get("/api/v1/memory/facts")

        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        assert "total" in data
        assert "has_more" in data

    def test_get_fact_by_id_not_found_returns_404(self):
        """Test: GET /memory/facts/{id} with invalid id returns 404."""
        response = client.get("/api/v1/memory/facts/nonexistent-fact-id")

        assert response.status_code == 404

    def test_delete_fact_not_found_returns_404(self):
        """Test: DELETE /memory/facts/{id} with invalid id returns 404."""
        response = client.delete("/api/v1/memory/facts/nonexistent-fact-id")

        assert response.status_code == 404

    def test_get_memory_stats_returns_stats(self):
        """Test: GET /memory/stats returns statistics."""
        response = client.get("/api/v1/memory/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_facts" in data
        assert "facts_by_type" in data
        assert "avg_importance" in data

    def test_get_facts_with_filters(self):
        """Test: GET /memory/facts with query parameters."""
        response = client.get(
            "/api/v1/memory/facts",
            params={
                "min_importance": 0.7,
                "fact_type": "preference",
                "limit": 10,
                "offset": 0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        assert data["limit"] == 10

class TestDocumentEndpoints:
    """Tests for /documents/* endpoints."""

    @pytest.mark.skip(reason="ChromaDB schema mismatch - known issue")
    def test_search_documents_returns_results(self):
        """Test: POST /documents/search returns search results."""
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "test query", "n_results": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_found" in data

class TestWebSearchEndpoint:
    """Tests for /search/web endpoint."""

    def test_web_search_invalid_query_returns_400(self):
        """Test: POST /search/web with empty query returns 400."""
        response = client.post(
            "/api/v1/search/web",
            json={"query": "", "max_results": 5}
        )

        assert response.status_code == 400

class TestChatEndpoints:
    """Tests for /chat/* endpoints."""

    def test_enhanced_chat_invalid_message_returns_400(self):
        """Test: POST /chat/enhanced with empty message returns 400."""
        response = client.post(
            "/api/v1/chat/enhanced",
            json={
                "session_id": "test-session-12345678",
                "message": ""
            }
        )

        assert response.status_code == 400

    def test_enhanced_chat_invalid_session_id_returns_400(self):
        """Test: POST /chat/enhanced with invalid session_id returns 400."""
        response = client.post(
            "/api/v1/chat/enhanced",
            json={
                "session_id": "bad",  # Too short
                "message": "Hello world"
            }
        )

        assert response.status_code == 400
        assert "session" in response.json()["detail"].lower()