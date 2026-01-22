"""
Unit tests for memory service
"""

import pytest

from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_add_message(test_db):
    """Test adding a message to conversation history"""
    service = MemoryService(test_db)

    message = await service.add_message(session_id="test-123", role="user", content="Hello!", tokens_used=5)

    assert message.id is not None
    assert message.content == "Hello!"
    assert message.role == "user"


@pytest.mark.asyncio
async def test_get_conversation_history(test_db):
    """Test retrieving conversation history"""
    service = MemoryService(test_db)

    # Add multiple messages
    for i in range(5):
        await service.add_message(session_id="test-123", role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")

    # Get history
    history = await service.get_conversation_history("test-123", limit=10)

    assert len(history) == 5
    assert history[0].content == "Message 0"  # Chronological order
    assert history[-1].content == "Message 4"


@pytest.mark.asyncio
async def test_add_and_search_facts(test_db):
    """Test adding and searching facts (Memorisator v2)"""
    from uuid import uuid4
    from app.models.memory_v2 import Fact

    service = MemoryService(test_db)

    # Add facts using v2 API
    facts_to_add = [
        Fact(fact_id=str(uuid4()), text="User likes Python", importance=0.8, confidence=0.9, fact_type="preference",
             source="test"),
        Fact(fact_id=str(uuid4()), text="User lives in Tel Aviv", importance=0.9, confidence=0.9, fact_type="personal",
             source="test"),
        Fact(fact_id=str(uuid4()), text="User enjoys coffee", importance=0.3, confidence=0.9, fact_type="preference",
             source="test"),
    ]
    await service.add_facts(facts_to_add)

    # Search for important facts
    important_facts = await service.get_important_facts(min_importance=0.7)
    assert len(important_facts) == 2
    assert all(f.importance >= 0.7 for f in important_facts)

    # Search by text
    python_facts = await service.search_facts("Python")
    assert len(python_facts) == 1
    assert "Python" in python_facts[0].text


@pytest.mark.asyncio
async def test_update_fact_usage(test_db):
    """Test updating fact usage statistics (Memorisator v2)"""
    from uuid import uuid4
    from app.models.memory_v2 import Fact

    service = MemoryService(test_db)

    # Add fact using v2 API
    facts = await service.add_facts([
        Fact(fact_id=str(uuid4()), text="Test fact for usage", importance=0.5, confidence=0.9, fact_type="test",
             source="test")
    ])
    fact = facts[0]
    initial_count = fact.usage_count

    # Update usage
    await service.update_fact_usage(str(fact.fact_id))

    # Verify
    updated_facts = await service.search_facts("Test fact for usage")
    assert len(updated_facts) == 1
    assert updated_facts[0].usage_count == initial_count + 1
    assert updated_facts[0].last_accessed is not None