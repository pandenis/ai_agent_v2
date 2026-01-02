"""
Integration tests for Sessions API endpoints.

Tests:
- POST /sessions (create)
- GET /sessions (list)
- GET /sessions/{id} (get one)
- GET /sessions/{id}/messages
- GET /sessions/{id}/facts
"""

import pytest


class TestCreateSession:
    """Tests for POST /sessions endpoint."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, client):
        """Test: POST /sessions creates new session."""
        # Arrange
        request_data = {
            "agent_name": "mistral"
        }
        
        # Act
        response = await client.post("/api/v1/sessions", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["agent_name"] == "mistral"

    @pytest.mark.asyncio
    async def test_create_session_without_agent(self, client):
        """Test: POST /sessions works without agent_name."""
        # Arrange
        request_data = {}
        
        # Act
        response = await client.post("/api/v1/sessions", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_create_session_invalid_agent_name(self, client):
        """Test: POST /sessions with dangerous chars returns 400."""
        # Arrange
        request_data = {
            "agent_name": "mistral; rm -rf /"
        }
        
        # Act
        response = await client.post("/api/v1/sessions", json=request_data)
        
        # Assert
        assert response.status_code == 400


class TestGetSessions:
    """Tests for GET /sessions endpoint."""

    @pytest.mark.asyncio
    async def test_get_sessions_empty(self, client):
        """Test: GET /sessions returns empty list initially."""
        # Act
        response = await client.get("/api/v1/sessions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_sessions_after_create(self, client):
        """Test: GET /sessions returns created sessions."""
        # Arrange - create a session first
        await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        
        # Act
        response = await client.get("/api/v1/sessions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_sessions_with_pagination(self, client):
        """Test: GET /sessions respects limit and skip."""
        # Arrange - create multiple sessions
        for i in range(3):
            await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        
        # Act
        response = await client.get("/api/v1/sessions?limit=2&skip=0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestGetSessionById:
    """Tests for GET /sessions/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, client):
        """Test: GET /sessions/{id} returns session details."""
        # Arrange - create session first
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get(f"/api/v1/sessions/{session_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        """Test: GET /sessions/{id} returns 404 for unknown session."""
        # Act
        response = await client.get("/api/v1/sessions/nonexistent-session-id")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSessionMessages:
    """Tests for GET /sessions/{session_id}/messages endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_messages_empty(self, client):
        """Test: GET /sessions/{id}/messages returns empty for new session."""
        # Arrange - create session first
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get(f"/api/v1/sessions/{session_id}/messages")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "messages" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_session_messages_not_found(self, client):
        """Test: GET /sessions/{id}/messages returns 404 for unknown session."""
        # Act
        response = await client.get("/api/v1/sessions/nonexistent-id/messages")
        
        # Assert
        assert response.status_code == 404


class TestGetSessionFacts:
    """Tests for GET /sessions/{session_id}/facts endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_facts_empty(self, client):
        """Test: GET /sessions/{id}/facts returns empty for new session."""
        # Arrange - create session first
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get(f"/api/v1/sessions/{session_id}/facts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "facts" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_session_facts_not_found(self, client):
        """Test: GET /sessions/{id}/facts returns 404 for unknown session."""
        # Act
        response = await client.get("/api/v1/sessions/nonexistent-id/facts")
        
        # Assert
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestSessionsWithMessages:
    """Tests for sessions with actual messages."""

    @pytest.mark.asyncio
    async def test_get_sessions_includes_message_count(self, client):
        """Test: GET /sessions includes message_count for each session."""
        # Arrange - create a session
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        assert create_response.status_code == 201
        
        # Act
        response = await client.get("/api/v1/sessions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Check first session has message_count field
        assert "message_count" in data[0]
        assert isinstance(data[0]["message_count"], int)

    @pytest.mark.asyncio
    async def test_get_sessions_message_count_is_zero_for_new_session(self, client):
        """Test: New session has message_count of 0."""
        # Arrange
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get("/api/v1/sessions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Find our session
        our_session = next((s for s in data if s["session_id"] == session_id), None)
        assert our_session is not None
        assert our_session["message_count"] == 0


class TestSessionFactsRetrieval:
    """Tests for session facts retrieval with actual facts."""

    @pytest.mark.asyncio
    async def test_get_session_facts_returns_fact_details(self, client):
        """Test: GET /sessions/{id}/facts returns proper fact structure."""
        # Arrange - create a session
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get(f"/api/v1/sessions/{session_id}/facts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "facts" in data
        assert isinstance(data["facts"], list)
        assert "total" in data
