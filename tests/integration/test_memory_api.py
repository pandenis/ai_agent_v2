"""
Integration tests for Memory/Memorisator API endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.memory_v2 import Fact, FactModel

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_session():
    """Create test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db_session):
    """Create test client with database override"""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_facts(test_db_session):
    """Create sample facts in test database"""
    facts = [
        FactModel(
            fact_id="fact-1",
            text="User is a Python developer",
            importance=0.9,
            confidence=0.95,
            tags=["programming", "python"],
            fact_type="static",
            source="conversation"
        ),
        FactModel(
            fact_id="fact-2",
            text="User lives in Tel Aviv",
            importance=0.8,
            confidence=0.9,
            tags=["location"],
            fact_type="static",
            source="conversation"
        ),
        FactModel(
            fact_id="fact-3",
            text="User loves AI",
            importance=0.7,
            confidence=0.85,
            tags=["preference", "ai"],
            fact_type="preference",
            source="conversation"
        ),
        FactModel(
            fact_id="fact-4",
            text="User planning trip to Athens",
            importance=0.6,
            confidence=0.8,
            tags=["travel", "event"],
            fact_type="event",
            source="conversation"
        )
    ]

    for fact in facts:
        test_db_session.add(fact)

    await test_db_session.commit()

    return facts


class TestMemoryStatsEndpoint:
    """Tests for GET /api/v1/memory/stats"""

    @pytest.mark.asyncio
    async def test_get_stats_empty_database(self, client):
        """Test stats with no facts"""
        response = await client.get("/api/v1/memory/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_facts"] == 0
        assert data["facts_by_type"] == {}
        assert data["avg_importance"] == 0.0

    @pytest.mark.asyncio
    async def test_get_stats_with_facts(self, client, sample_facts):
        """Test stats with facts in database"""
        response = await client.get("/api/v1/memory/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_facts"] == 4
        assert data["facts_by_type"]["static"] == 2
        assert data["facts_by_type"]["preference"] == 1
        assert data["facts_by_type"]["event"] == 1
        assert data["avg_importance"] == 0.75  # (0.9 + 0.8 + 0.7 + 0.6) / 4


class TestMemoryFactsListEndpoint:
    """Tests for GET /api/v1/memory/facts"""

    @pytest.mark.asyncio
    async def test_get_facts_empty_database(self, client):
        """Test getting facts from empty database"""
        response = await client.get("/api/v1/memory/facts")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert data["facts"] == []
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_all_facts(self, client, sample_facts):
        """Test getting all facts without filters"""
        response = await client.get("/api/v1/memory/facts")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4
        assert len(data["facts"]) == 4
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_facts_with_importance_filter(self, client, sample_facts):
        """Test filtering by minimum importance"""
        response = await client.get("/api/v1/memory/facts?min_importance=0.8")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2  # Only facts with importance >= 0.8
        assert all(fact["importance"] >= 0.8 for fact in data["facts"])

    @pytest.mark.asyncio
    async def test_get_facts_with_type_filter(self, client, sample_facts):
        """Test filtering by fact type"""
        response = await client.get("/api/v1/memory/facts?fact_type=static")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert all(fact["fact_type"] == "static" for fact in data["facts"])

    @pytest.mark.asyncio
    async def test_get_facts_with_tags_filter(self, client, sample_facts):
        """Test filtering by tags"""
        response = await client.get("/api/v1/memory/facts?tags=programming")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        # Check that at least one fact has the tag
        assert any("programming" in fact["tags"] for fact in data["facts"])

    @pytest.mark.asyncio
    async def test_get_facts_with_pagination(self, client, sample_facts):
        """Test pagination with limit and offset"""
        # Get first 2 facts
        response = await client.get("/api/v1/memory/facts?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["facts"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["has_more"] is True

        # Get next 2 facts
        response = await client.get("/api/v1/memory/facts?limit=2&offset=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["facts"]) == 2
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_facts_combined_filters(self, client, sample_facts):
        """Test combining multiple filters"""
        response = await client.get(
            "/api/v1/memory/facts?min_importance=0.7&fact_type=static"
        )

        assert response.status_code == 200
        data = response.json()

        # Should get facts that are both static AND importance >= 0.7
        assert all(
            fact["fact_type"] == "static" and fact["importance"] >= 0.7
            for fact in data["facts"]
        )


class TestMemoryFactByIdEndpoint:
    """Tests for GET /api/v1/memory/facts/{id}"""

    @pytest.mark.asyncio
    async def test_get_fact_by_id_exists(self, client, sample_facts):
        """Test getting an existing fact by ID"""
        response = await client.get("/api/v1/memory/facts/fact-1")

        assert response.status_code == 200
        data = response.json()

        assert data["fact_id"] == "fact-1"
        assert data["text"] == "User is a Python developer"
        assert data["importance"] == 0.9
        assert "programming" in data["tags"]

    @pytest.mark.asyncio
    async def test_get_fact_by_id_not_found(self, client, sample_facts):
        """Test getting a non-existent fact"""
        response = await client.get("/api/v1/memory/facts/non-existent-id")

        assert response.status_code == 404
        data = response.json()

        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_fact_response_structure(self, client, sample_facts):
        """Test that response has all required fields"""
        response = await client.get("/api/v1/memory/facts/fact-1")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        required_fields = [
            "fact_id", "text", "importance", "confidence",
            "tags", "fact_type", "source", "created", "updated"
        ]
        for field in required_fields:
            assert field in data


class TestMemoryDeleteFactEndpoint:
    """Tests for DELETE /api/v1/memory/facts/{id}"""

    @pytest.mark.asyncio
    async def test_delete_fact_exists(self, client, sample_facts):
        """Test deleting an existing fact"""
        # First verify fact exists
        response = await client.get("/api/v1/memory/facts/fact-4")
        assert response.status_code == 200

        # Delete the fact
        response = await client.delete("/api/v1/memory/facts/fact-4")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["fact_id"] == "fact-4"
        assert "successfully" in data["message"].lower()

        # Verify fact is deleted
        response = await client.get("/api/v1/memory/facts/fact-4")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_fact_not_found(self, client, sample_facts):
        """Test deleting a non-existent fact"""
        response = await client.delete("/api/v1/memory/facts/non-existent-id")

        assert response.status_code == 404
        data = response.json()

        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_fact_updates_stats(self, client, sample_facts):
        """Test that deletion updates statistics"""
        # Get initial stats
        response = await client.get("/api/v1/memory/stats")
        initial_total = response.json()["total_facts"]

        # Delete a fact
        await client.delete("/api/v1/memory/facts/fact-1")

        # Check stats updated
        response = await client.get("/api/v1/memory/stats")
        new_total = response.json()["total_facts"]

        assert new_total == initial_total - 1


class TestMemoryAPIEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_facts_ordered_by_importance(self, client, sample_facts):
        """Test that facts are returned in descending importance order"""
        response = await client.get("/api/v1/memory/facts")

        assert response.status_code == 200
        data = response.json()

        importances = [fact["importance"] for fact in data["facts"]]

        # Check that list is sorted in descending order
        assert importances == sorted(importances, reverse=True)