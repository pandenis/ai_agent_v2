"""
Tests for session endpoint validation
TDD: BUG-03 - rename_session skips validation
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRenameSessionValidation:
    """Tests for rename_session input validation"""

    def test_rename_session_rejects_shell_injection(self):
        """
        BUG-03: rename_session should validate agent_name like create_session does
        """
        # Create a valid session first
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "mistral"}
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # Try to rename with dangerous characters
        response = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"agent_name": "test; rm -rf /"}
        )
        
        # Should be rejected (400 Bad Request)
        assert response.status_code == 400

    def test_rename_session_rejects_backticks(self):
        """Test: Backtick command substitution rejected"""
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "groq"}
        )
        session_id = create_response.json()["session_id"]
        
        response = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"agent_name": "test`whoami`"}
        )
        
        assert response.status_code == 400

    def test_rename_session_accepts_valid_names(self):
        """Test: Valid names should work"""
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "initial"}
        )
        session_id = create_response.json()["session_id"]
        
        # Valid names should be accepted
        response = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"agent_name": "My Chat Session"}
        )
        
        assert response.status_code == 200
        assert response.json()["agent_name"] == "My Chat Session"
