"""
TDD Tests for DELETE /api/v1/sessions/{session_id}

Tests verify:
1. Session deletion works
2. Related messages are also deleted (cascade)
3. Proper error handling
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


class TestDeleteSessionEndpoint:
    """Tests for DELETE /api/v1/sessions/{session_id}"""

    @pytest.mark.asyncio
    async def test_delete_session_returns_204(self, test_db):
        """Test: Delete existing session returns 204 No Content"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session first
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            assert create_response.status_code == 201
            session_id = create_response.json()["session_id"]

            # Delete the session
            response = await client.delete(f"/api/v1/sessions/{session_id}")
            assert response.status_code == 204

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_session_not_found_returns_404(self, test_db):
        """Test: Delete non-existent session returns 404"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/v1/sessions/non-existent-id")
            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_session_actually_removes(self, test_db):
        """Test: Deleted session is no longer retrievable"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            session_id = create_response.json()["session_id"]

            # Delete it
            await client.delete(f"/api/v1/sessions/{session_id}")

            # Try to get it - should 404
            get_response = await client.get(f"/api/v1/sessions/{session_id}")
            assert get_response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_session_removes_messages(self, test_db):
        """Test: Deleting session also removes its messages"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            session_id = create_response.json()["session_id"]

            # Get messages count before (should be 0, but endpoint should work)
            messages_before = await client.get(f"/api/v1/sessions/{session_id}/messages")
            assert messages_before.status_code == 200

            # Delete the session
            delete_response = await client.delete(f"/api/v1/sessions/{session_id}")
            assert delete_response.status_code == 204

            # Try to get messages - should 404 (session gone)
            messages_after = await client.get(f"/api/v1/sessions/{session_id}/messages")
            assert messages_after.status_code == 404

        app.dependency_overrides.clear()


class TestRenameSessionEndpoint:
    """Tests for PATCH /api/v1/sessions/{session_id}"""

    @pytest.mark.asyncio
    async def test_rename_session_returns_200(self, test_db):
        """Test: Rename existing session returns 200"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session first
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            assert create_response.status_code == 201
            session_id = create_response.json()["session_id"]

            # Rename the session
            response = await client.patch(
                f"/api/v1/sessions/{session_id}",
                json={"agent_name": "My Custom Chat"}
            )
            assert response.status_code == 200
            assert response.json()["agent_name"] == "My Custom Chat"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rename_session_not_found_returns_404(self, test_db):
        """Test: Rename non-existent session returns 404"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/sessions/non-existent-id",
                json={"agent_name": "New Name"}
            )
            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rename_session_persists(self, test_db):
        """Test: Renamed session keeps new name"""
        app.dependency_overrides[get_db] = lambda: test_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a session
            create_response = await client.post(
                "/api/v1/sessions",
                json={"agent_name": "mistral"}
            )
            session_id = create_response.json()["session_id"]

            # Rename it
            await client.patch(
                f"/api/v1/sessions/{session_id}",
                json={"agent_name": "Renamed Session"}
            )

            # Get it again - should have new name
            get_response = await client.get(f"/api/v1/sessions/{session_id}")
            assert get_response.status_code == 200
            assert get_response.json()["agent_name"] == "Renamed Session"

        app.dependency_overrides.clear()