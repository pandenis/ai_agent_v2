"""
Unit tests for Memorisator Fact model
"""
import pytest
from datetime import datetime
from app.models.memory_v2 import Fact, FactModel, ContextMap, ContextMapModel


def test_fact_dataclass_creation():
    """Test creating a Fact dataclass"""
    fact = Fact(
        fact_id="test-123",
        text="User loves Python programming",
        importance=0.8,
        confidence=0.9,
        tags=["programming", "python"],
        fact_type="preference"
    )
    
    assert fact.fact_id == "test-123"
    assert fact.text == "User loves Python programming"
    assert fact.importance == 0.8
    assert fact.confidence == 0.9
    assert "programming" in fact.tags
    assert fact.fact_type == "preference"
    assert fact.source == "conversation"  # default
    assert fact.usage_count == 0  # default


def test_fact_defaults():
    """Test Fact dataclass with default values"""
    fact = Fact(
        fact_id="test-456",
        text="Test fact"
    )
    
    assert fact.importance == 0.5
    assert fact.confidence == 0.8
    assert fact.tags == []
    assert fact.fact_type == "static"
    assert fact.source == "conversation"
    assert fact.needs_update is False
    assert fact.update_frequency is None


@pytest.mark.asyncio
async def test_fact_model_create(test_db):
    """Test creating FactModel in database"""
    fact = FactModel(
        fact_id="test-789",
        text="User planning trip to Athens",
        importance=0.8,
        tags=["travel", "athens"],
        fact_type="event"
    )
    
    test_db.add(fact)
    await test_db.commit()
    await test_db.refresh(fact)
    
    assert fact.id is not None
    assert fact.fact_id == "test-789"
    assert fact.text == "User planning trip to Athens"
    assert isinstance(fact.created, datetime)


@pytest.mark.asyncio
async def test_fact_model_to_dataclass(test_db):
    """Test converting FactModel to Fact dataclass"""
    fact_model = FactModel(
        fact_id="test-999",
        text="Test conversion",
        importance=0.7,
        tags=["test"]
    )
    
    test_db.add(fact_model)
    await test_db.commit()
    await test_db.refresh(fact_model)
    
    # Convert to dataclass
    fact_dc = fact_model.to_dataclass()
    
    assert isinstance(fact_dc, Fact)
    assert fact_dc.fact_id == "test-999"
    assert fact_dc.text == "Test conversion"
    assert fact_dc.importance == 0.7
    assert fact_dc.tags == ["test"]


@pytest.mark.asyncio
async def test_fact_model_update_timestamp(test_db):
    """Test that updated timestamp changes on update"""
    fact = FactModel(
        fact_id="test-update",
        text="Original text"
    )
    
    test_db.add(fact)
    await test_db.commit()
    await test_db.refresh(fact)
    
    original_updated = fact.updated
    
    # Update the fact
    fact.text = "Updated text"
    await test_db.commit()
    await test_db.refresh(fact)
    
    assert fact.updated > original_updated


def test_context_map_creation():
    """Test creating a ContextMap"""
    context_map = ContextMap(
        map_id="trip-athens-2025",
        topic="Trip to Athens",
        fact_ids=["fact-1", "fact-2"],
        sub_nodes={
            "planning": ["fact-1"],
            "logistics": ["fact-2"]
        }
    )
    
    assert context_map.map_id == "trip-athens-2025"
    assert context_map.topic == "Trip to Athens"
    assert len(context_map.fact_ids) == 2
    assert "planning" in context_map.sub_nodes


@pytest.mark.asyncio
async def test_context_map_model_create(test_db):
    """Test creating ContextMapModel in database"""
    context_map = ContextMapModel(
        map_id="test-map-123",
        topic="Test Context",
        fact_ids=["fact-1", "fact-2"]
    )
    
    test_db.add(context_map)
    await test_db.commit()
    await test_db.refresh(context_map)
    
    assert context_map.id is not None
    assert context_map.map_id == "test-map-123"
    assert context_map.topic == "Test Context"
    assert len(context_map.fact_ids) == 2


def test_fact_type_validation():
    """Test that fact types are set correctly"""
    fact_types = ["static", "weather", "event", "preference", "knowledge"]
    
    for fact_type in fact_types:
        fact = Fact(
            fact_id=f"test-{fact_type}",
            text=f"Test {fact_type}",
            fact_type=fact_type
        )
        assert fact.fact_type == fact_type


def test_fact_importance_range():
    """Test that importance values are in valid range"""
    # Test valid importance
    fact = Fact(
        fact_id="test-importance",
        text="Test",
        importance=0.5
    )
    assert 0.0 <= fact.importance <= 1.0
    
    # Test edge cases
    fact_low = Fact(fact_id="low", text="Low", importance=0.0)
    fact_high = Fact(fact_id="high", text="High", importance=1.0)
    
    assert fact_low.importance == 0.0
    assert fact_high.importance == 1.0


@pytest.mark.asyncio
async def test_fact_model_json_fields(test_db):
    """Test that JSON fields work correctly"""
    fact = FactModel(
        fact_id="test-json",
        text="Test JSON fields",
        tags=["tag1", "tag2", "tag3"],
        related_fact_ids=["fact-1", "fact-2"],
        context_maps=["map-1"],
        meta_data={"key": "value", "number": 42}
    )
    
    test_db.add(fact)
    await test_db.commit()
    await test_db.refresh(fact)
    
    assert len(fact.tags) == 3
    assert "tag2" in fact.tags
    assert len(fact.related_fact_ids) == 2
    assert fact.meta_data["key"] == "value"
    assert fact.meta_data["number"] == 42


@pytest.mark.asyncio
async def test_fact_usage_tracking(test_db):
    """Test that usage_count can be incremented"""
    fact = FactModel(
        fact_id="test-usage",
        text="Test usage tracking"
    )
    
    test_db.add(fact)
    await test_db.commit()
    await test_db.refresh(fact)
    
    assert fact.usage_count == 0
    
    # Increment usage
    fact.usage_count += 1
    fact.last_accessed = datetime.utcnow()
    await test_db.commit()
    await test_db.refresh(fact)
    
    assert fact.usage_count == 1
    assert fact.last_accessed is not None
