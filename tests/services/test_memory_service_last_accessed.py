"""
Test for BUG-02: update_fact_usage uses wrong attribute name
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import select

from app.models.memory_v2 import Fact, FactModel
from app.services.memory_service import MemoryService


class TestUpdateFactUsageAttribute:
    """Test that update_fact_usage uses correct attribute"""

    @pytest.mark.asyncio
    async def test_update_fact_usage_uses_last_accessed(self, test_db):
        """
        BUG-02: update_fact_usage should use last_accessed, not last_used
        
        FactModel has 'last_accessed' field, not 'last_used'
        """
        # Arrange
        memory_service = MemoryService(test_db)
        
        fact = Fact(
            fact_id="test-last-accessed",
            text="Test fact for attribute check",
            importance=0.8,
        )
        await memory_service.add_facts([fact])
        
        # Act - This should NOT raise AttributeError
        await memory_service.update_fact_usage("test-last-accessed")
        
        # Assert - Verify last_accessed was updated
        result = await test_db.execute(
            select(FactModel).where(FactModel.fact_id == "test-last-accessed")
        )
        updated_fact = result.scalar_one()
        
        assert updated_fact.usage_count == 1
        assert updated_fact.last_accessed is not None

    @pytest.mark.asyncio
    async def test_update_fact_usage_increments_count(self, test_db):
        """Test usage_count increments correctly"""
        memory_service = MemoryService(test_db)
        
        fact = Fact(
            fact_id="test-increment",
            text="Test counting",
            importance=0.5,
        )
        await memory_service.add_facts([fact])
        
        # Call 3 times
        await memory_service.update_fact_usage("test-increment")
        await memory_service.update_fact_usage("test-increment")
        await memory_service.update_fact_usage("test-increment")
        
        result = await test_db.execute(
            select(FactModel).where(FactModel.fact_id == "test-increment")
        )
        updated_fact = result.scalar_one()
        
        assert updated_fact.usage_count == 3
