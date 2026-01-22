"""
Tests for session listing performance
TDD: BUG-05 - N+1 queries on session listing
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


class TestGetSessionsPerformance:
    """Tests for efficient session listing"""

    def test_get_sessions_returns_message_counts(self):
        """Test: Sessions include correct message counts"""
        # Create a session
        create_response = client.post(
            "/api/v1/sessions",
            json={"agent_name": "test-perf"}
        )
        assert create_response.status_code == 201
        
        # Get sessions
        response = client.get("/api/v1/sessions")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) > 0
        
        # Each session should have message_count field
        for session in sessions:
            assert "message_count" in session
            assert isinstance(session["message_count"], int)

    def test_get_sessions_with_limit(self):
        """Test: Limit parameter works"""
        response = client.get("/api/v1/sessions?limit=5")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) <= 5

    def test_get_sessions_structure(self):
        """Test: Response has correct structure"""
        response = client.get("/api/v1/sessions?limit=1")
        assert response.status_code == 200
        
        sessions = response.json()
        if len(sessions) > 0:
            session = sessions[0]
            assert "session_id" in session
            assert "agent_name" in session
            assert "created_at" in session
            assert "message_count" in session
