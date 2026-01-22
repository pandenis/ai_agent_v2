"""
Tests for session endpoint validation
TDD: BUG-03 - rename_session skips validation
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


class TestRenameSessionValidation:
    """Tests for rename_session input validation"""

    @pytest.mark.asyncio
    async def test_rename_session_rejects_shell_injection(self, test_db):
        """
        BUG-03: rename_session should validate agent_name like create_session does
        """
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a valid session first
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            assert create_response.status_code == 201
            session_id = create_response.json()["session_id"]
            
            # Try to rename with dangerous characters
            response = await client.patch(
                f"/api/v1/sessions/{session_id}",
                json={"agent_name": "test; rm -rf /"}
            )
            
            # Should be rejected (400 Bad Request)
            assert response.status_code == 400
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rename_session_rejects_backticks(self, test_db):
        """Test: Backtick command substitution rejected"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "groq"}
            )
            session_id = create_response.json()["session_id"]
            
            response = await client.patch(
                f"/api/v1/sessions/{session_id}",
                json={"agent_name": "test$(whoami)"}
            )
            
            assert response.status_code == 400
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rename_session_accepts_valid_names(self, test_db):
        """Test: Valid names should work"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "initial"}
            )
            session_id = create_response.json()["session_id"]
            
            # Valid names should be accepted
            response = await client.patch(
                f"/api/v1/sessions/{session_id}",
                json={"agent_name": "My Chat Session"}
            )
            
            assert response.status_code == 200
            assert response.json()["agent_name"] == "My Chat Session"
        
        app.dependency_overrides.clear()
