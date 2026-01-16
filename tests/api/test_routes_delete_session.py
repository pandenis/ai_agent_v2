"""
TDD Tests for DELETE /api/v1/sessions/{session_id}

Tests verify:
1. Session deletion works
2. Related messages are also deleted (cascade)
3. Proper error handling
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestDeleteSessionEndpoint:
    """Tests for DELETE /api/v1/sessions/{session_id}"""

    def test_delete_session_returns_204(self):
        """Test: Delete existing session returns 204 No Content"""
        # Create a session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # Delete the session
        response = client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 204

    def test_delete_session_not_found_returns_404(self):
        """Test: Delete non-existent session returns 404"""
        response = client.delete("/api/v1/sessions/non-existent-id")
        assert response.status_code == 404

    def test_delete_session_actually_removes(self):
        """Test: Deleted session is no longer retrievable"""
        # Create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        session_id = create_response.json()["session_id"]
        
        # Delete it
        client.delete(f"/api/v1/sessions/{session_id}")
        
        # Try to get it - should 404
        get_response = client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == 404

    def test_delete_session_removes_messages(self):
        """Test: Deleting session also removes its messages"""
        # Create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        session_id = create_response.json()["session_id"]
        
        # Get messages count before (should be 0, but endpoint should work)
        messages_before = client.get(f"/api/v1/sessions/{session_id}/messages")
        assert messages_before.status_code == 200
        
        # Delete the session
        delete_response = client.delete(f"/api/v1/sessions/{session_id}")
        assert delete_response.status_code == 204
        
        # Try to get messages - should 404 (session gone)
        messages_after = client.get(f"/api/v1/sessions/{session_id}/messages")
        assert messages_after.status_code == 404


class TestRenameSessionEndpoint:
    """Tests for PATCH /api/v1/sessions/{session_id}"""

    def test_rename_session_returns_200(self):
        """Test: Rename existing session returns 200"""
        # Create a session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # Rename the session
        response = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"agent_name": "My Custom Chat"}
        )
        assert response.status_code == 200
        assert response.json()["agent_name"] == "My Custom Chat"

    def test_rename_session_not_found_returns_404(self):
        """Test: Rename non-existent session returns 404"""
        response = client.patch(
            "/api/v1/sessions/non-existent-id",
            json={"agent_name": "New Name"}
        )
        assert response.status_code == 404

    def test_rename_session_persists(self):
        """Test: Renamed session keeps new name"""
        # Create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        session_id = create_response.json()["session_id"]
        
        # Rename it
        client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"agent_name": "Renamed Session"}
        )
        
        # Get it again - should have new name
        get_response = client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["agent_name"] == "Renamed Session"
