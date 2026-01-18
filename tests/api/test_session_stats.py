"""
TDD Tests for GET /api/v1/sessions/{session_id}/stats
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


class TestSessionStatsEndpoint:
    """Tests for session statistics endpoint"""

    @pytest.mark.asyncio
    async def test_session_stats_returns_200(self, test_db):
        """Test: Session stats endpoint returns 200 for existing session"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session first
            create_resp = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            session_id = create_resp.json()["session_id"]
            
            # Get stats
            response = await client.get(f"/api/v1/sessions/{session_id}/stats")
            assert response.status_code == 200
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_session_stats_returns_expected_fields(self, test_db):
        """Test: Response contains all expected fields"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session
            create_resp = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            session_id = create_resp.json()["session_id"]
            
            # Get stats
            response = await client.get(f"/api/v1/sessions/{session_id}/stats")
            data = response.json()
            
            assert "session_id" in data
            assert "message_count" in data
            assert "user_messages" in data
            assert "assistant_messages" in data
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_session_stats_not_found(self, test_db):
        """Test: Returns 404 for non-existent session"""
        app.dependency_overrides[get_db] = lambda: test_db
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/sessions/non-existent-id/stats")
            assert response.status_code == 404
        
        app.dependency_overrides.clear()
