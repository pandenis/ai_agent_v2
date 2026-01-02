"""
Integration tests for edge cases and uncovered paths.

Tests targeting specific uncovered lines in routes.py.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAgentSelectEdgeCases:
    """Edge case tests for /agents/select endpoint."""

    @pytest.mark.asyncio
    async def test_select_agent_config_not_found(self, client):
        """Test: POST /agents/select returns 404 when agent config not found."""
        # Arrange
        request_data = {
            "prompt": "Test prompt for agent selection"
        }
        
        # Patch at the correct location - inside the function's import
        with patch('app.core.agent_config.agent_registry') as mock_registry:
            mock_registry.get_agent_config.return_value = None
            
            # Act
            response = await client.post("/api/v1/agents/select", json=request_data)
        
        # Assert
        assert response.status_code == 404
        assert "No suitable agent found" in response.json()["detail"]


class TestSessionsWithMessageCounts:
    """Tests for sessions list with message counts."""

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
    async def test_get_sessions_message_count_zero_for_new(self, client):
        """Test: New session has message_count of 0."""
        # Arrange
        create_response = await client.post("/api/v1/sessions", json={"agent_name": "mistral"})
        session_id = create_response.json()["session_id"]
        
        # Act
        response = await client.get("/api/v1/sessions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        our_session = next((s for s in data if s["session_id"] == session_id), None)
        assert our_session is not None
        assert our_session["message_count"] == 0


class TestSessionFactsRetrieval:
    """Tests for session facts retrieval."""

    @pytest.mark.asyncio
    async def test_get_session_facts_structure(self, client):
        """Test: GET /sessions/{id}/facts returns proper structure."""
        # Arrange
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
        assert data["total"] == 0  # New session has no facts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
