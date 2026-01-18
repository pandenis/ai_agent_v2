"""
TDD Tests for GET /api/v1/system/cache-stats
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestCacheStatsEndpoint:
    """Tests for cache statistics endpoint"""

    @pytest.mark.asyncio
    async def test_cache_stats_returns_200(self):
        """Test: Cache stats endpoint returns 200"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/system/cache-stats")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cache_stats_returns_expected_fields(self):
        """Test: Response contains all expected fields"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/system/cache-stats")
            data = response.json()
            
            assert "hits" in data
            assert "misses" in data
            assert "hit_rate" in data
            assert "size" in data
            assert "max_size" in data

    @pytest.mark.asyncio
    async def test_cache_stats_types(self):
        """Test: Fields have correct types"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/system/cache-stats")
            data = response.json()
            
            assert isinstance(data["hits"], int)
            assert isinstance(data["misses"], int)
            assert isinstance(data["hit_rate"], float)
            assert isinstance(data["size"], int)
            assert isinstance(data["max_size"], int)
