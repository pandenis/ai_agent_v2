"""
Unit tests for Fact TTL (Time-To-Live) fields

Task 3.1: Add `expires_at` and `ttl_days` fields to FactModel
"""

from datetime import datetime, timedelta

import pytest


class TestFactDataclassTTLFields:
    """Test TTL fields on Fact dataclass"""

    def test_fact_has_ttl_days_field(self):
        """Test: Fact dataclass has ttl_days field"""
        from app.models.memory_v2 import Fact

        # Arrange & Act
        fact = Fact(
            fact_id="test-ttl-1",
            text="User prefers dark mode",
            ttl_days=30
        )

        # Assert
        assert hasattr(fact, "ttl_days")
        assert fact.ttl_days == 30

    def test_fact_ttl_days_default_none(self):
        """Test: ttl_days defaults to None (never expires)"""
        from app.models.memory_v2 import Fact

        # Arrange & Act
        fact = Fact(
            fact_id="test-ttl-2",
            text="User's name is Denis"
        )

        # Assert
        assert fact.ttl_days is None

    def test_fact_has_expires_at_field(self):
        """Test: Fact dataclass has expires_at field"""
        from app.models.memory_v2 import Fact

        # Arrange
        expiry = datetime.now() + timedelta(days=30)

        # Act
        fact = Fact(
            fact_id="test-expires-1",
            text="Weather is sunny",
            expires_at=expiry
        )

        # Assert
        assert hasattr(fact, "expires_at")
        assert fact.expires_at == expiry

    def test_fact_expires_at_default_none(self):
        """Test: expires_at defaults to None (never expires)"""
        from app.models.memory_v2 import Fact

        # Arrange & Act
        fact = Fact(
            fact_id="test-expires-2",
            text="User lives in Tel Aviv"
        )

        # Assert
        assert fact.expires_at is None

class TestFactModelTTLFields:
    """Test TTL fields on FactModel SQLAlchemy model"""

    @pytest.mark.asyncio
    async def test_fact_model_has_ttl_days_column(self, test_db):
        """Test: FactModel has ttl_days column"""
        from app.models.memory_v2 import FactModel

        # Arrange & Act
        fact = FactModel(
            fact_id="model-ttl-1",
            text="Test fact with TTL",
            ttl_days=30
        )

        test_db.add(fact)
        await test_db.commit()
        await test_db.refresh(fact)

        # Assert
        assert fact.ttl_days == 30

    @pytest.mark.asyncio
    async def test_fact_model_has_expires_at_column(self, test_db):
        """Test: FactModel has expires_at column"""
        from app.models.memory_v2 import FactModel

        # Arrange
        expiry = datetime.utcnow() + timedelta(days=30)

        # Act
        fact = FactModel(
            fact_id="model-expires-1",
            text="Expiring fact",
            expires_at=expiry
        )

        test_db.add(fact)
        await test_db.commit()
        await test_db.refresh(fact)

        # Assert
        assert fact.expires_at is not None
        # Allow 1 second tolerance for DB operations
        assert abs((fact.expires_at - expiry).total_seconds()) < 1