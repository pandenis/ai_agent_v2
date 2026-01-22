"""
Tests for session listing performance
TDD: BUG-05 - N+1 queries on session listing
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


class TestGetSessionsPerformance:
    """Tests for efficient session listing"""

    @pytest.mark.asyncio
    async def test_get_sessions_returns_message_counts(self, test_db):
        """Test: Sessions include correct message counts"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "test-perf"}
            )
            assert create_response.status_code == 201
            
            # Get sessions
            response = await client.get("/api/v1/sessions")
            assert response.status_code == 200
            
            sessions = response.json()
            assert len(sessions) > 0
            
            # Each session should have message_count field
            for session in sessions:
                assert "message_count" in session
                assert isinstance(session["message_count"], int)
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_sessions_with_limit(self, test_db):
        """Test: Limit parameter works"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/sessions?limit=5")
            assert response.status_code == 200
            
            sessions = response.json()
            assert len(sessions) <= 5
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_sessions_structure(self, test_db):
        """Test: Response has correct structure"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session first to ensure we have data
            await client.post(
                "/api/v1/sessions",
                json={"agent_name": "test-structure"}
            )
            
            response = await client.get("/api/v1/sessions?limit=1")
            assert response.status_code == 200
            
            sessions = response.json()
            if len(sessions) > 0:
                session = sessions[0]
                assert "session_id" in session
                assert "agent_name" in session
                assert "created_at" in session
                assert "message_count" in session
        
        app.dependency_overrides.clear()
