"""
Unit tests for MemoryCleanupService

Task 3.3: Implement MemoryCleanupService with expiration logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock


class TestMemoryCleanupServiceInit:
    """Test MemoryCleanupService initialization"""

    def test_cleanup_service_exists(self):
        """Test: MemoryCleanupService class exists"""
        from app.services.memory_cleanup_service import MemoryCleanupService

        assert MemoryCleanupService is not None

    def test_cleanup_service_requires_db_session(self):
        """Test: MemoryCleanupService requires db session"""
        from app.services.memory_cleanup_service import MemoryCleanupService

        mock_db = MagicMock()
        service = MemoryCleanupService(db=mock_db)

        assert service.db == mock_db

class TestGetExpiredFacts:
    """Test get_expired_facts method"""

    @pytest.mark.asyncio
    async def test_get_expired_facts_returns_list(self, test_db):
        """Test: get_expired_facts returns list of expired facts"""
        from app.services.memory_cleanup_service import MemoryCleanupService

        service = MemoryCleanupService(db=test_db)

        # Should return a list (empty when no expired facts)
        result = await service.get_expired_facts()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_expired_facts_queries_by_expires_at(self, test_db):
        """Test: get_expired_facts finds facts with expires_at in the past"""
        from app.services.memory_cleanup_service import MemoryCleanupService
        from app.models.memory_v2 import FactModel

        # Arrange - create expired and non-expired facts
        now = datetime.utcnow()

        expired_fact = FactModel(
            fact_id="expired-1",
            text="Old weather info",
            fact_type="weather",
            expires_at=now - timedelta(days=1)  # Expired yesterday
        )

        valid_fact = FactModel(
            fact_id="valid-1",
            text="Current preference",
            fact_type="preference",
            expires_at=now + timedelta(days=30)  # Expires in 30 days
        )

        permanent_fact = FactModel(
            fact_id="permanent-1",
            text="User's name",
            fact_type="static",
            expires_at=None  # Never expires
        )

        test_db.add_all([expired_fact, valid_fact, permanent_fact])
        await test_db.commit()

        service = MemoryCleanupService(db=test_db)

        # Act
        result = await service.get_expired_facts()

        # Assert
        assert len(result) == 1
        assert result[0].fact_id == "expired-1"

class TestCleanupExpiredFacts:
    """Test cleanup_expired_facts method"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_facts_deletes_expired(self, test_db):
        """Test: cleanup_expired_facts removes expired facts from database"""
        from app.services.memory_cleanup_service import MemoryCleanupService
        from app.models.memory_v2 import FactModel
        from sqlalchemy import select

        # Arrange
        now = datetime.utcnow()

        expired_fact = FactModel(
            fact_id="expired-1",
            text="Old weather",
            fact_type="weather",
            expires_at=now - timedelta(days=1)
        )

        valid_fact = FactModel(
            fact_id="valid-1",
            text="Current info",
            fact_type="static",
            expires_at=None
        )

        test_db.add_all([expired_fact, valid_fact])
        await test_db.commit()

        service = MemoryCleanupService(db=test_db)

        # Act
        deleted_count = await service.cleanup_expired_facts()

        # Assert
        assert deleted_count == 1

        # Verify expired fact is gone
        result = await test_db.execute(select(FactModel))
        remaining = list(result.scalars().all())
        assert len(remaining) == 1
        assert remaining[0].fact_id == "valid-1"

    @pytest.mark.asyncio
    async def test_cleanup_returns_zero_when_none_expired(self, test_db):
        """Test: cleanup_expired_facts returns 0 when no facts expired"""
        from app.services.memory_cleanup_service import MemoryCleanupService
        from app.models.memory_v2 import FactModel

        # Arrange - only non-expired facts
        now = datetime.utcnow()

        valid_fact = FactModel(
            fact_id="valid-1",
            text="Current info",
            fact_type="preference",
            expires_at=now + timedelta(days=30)
        )

        test_db.add(valid_fact)
        await test_db.commit()

        service = MemoryCleanupService(db=test_db)

        # Act
        deleted_count = await service.cleanup_expired_facts()

        # Assert
        assert deleted_count == 0


class TestGetCleanupStats:
    """Test get_cleanup_stats method"""

    @pytest.mark.asyncio
    async def test_get_cleanup_stats_returns_counts(self, test_db):
        """Test: get_cleanup_stats returns expired count and breakdown"""
        from app.services.memory_cleanup_service import MemoryCleanupService
        from app.models.memory_v2 import FactModel

        # Arrange
        now = datetime.utcnow()

        # 2 expired weather facts
        test_db.add(FactModel(
            fact_id="expired-w1",
            text="Old weather 1",
            fact_type="weather",
            expires_at=now - timedelta(days=1)
        ))
        test_db.add(FactModel(
            fact_id="expired-w2",
            text="Old weather 2",
            fact_type="weather",
            expires_at=now - timedelta(days=2)
        ))

        # 1 expired event fact
        test_db.add(FactModel(
            fact_id="expired-e1",
            text="Old event",
            fact_type="event",
            expires_at=now - timedelta(days=1)
        ))

        # 1 valid fact
        test_db.add(FactModel(
            fact_id="valid-1",
            text="Valid",
            fact_type="static",
            expires_at=None
        ))

        await test_db.commit()

        service = MemoryCleanupService(db=test_db)

        # Act
        stats = await service.get_cleanup_stats()

        # Assert
        assert stats["total_expired"] == 3
        assert stats["by_type"]["weather"] == 2
        assert stats["by_type"]["event"] == 1