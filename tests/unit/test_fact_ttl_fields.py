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