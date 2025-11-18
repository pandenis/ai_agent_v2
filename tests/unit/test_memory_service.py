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
    """Test adding and searching facts"""
    service = MemoryService(test_db)

    # Add facts
    await service.add_fact("User likes Python", importance=0.8, tags=["programming"])
    await service.add_fact("User lives in Tel Aviv", importance=0.9, tags=["personal"])
    await service.add_fact("User enjoys coffee", importance=0.3, tags=["preference"])

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
    """Test updating fact usage statistics"""
    service = MemoryService(test_db)

    # Add fact
    fact = await service.add_fact("Test fact", importance=0.5)
    initial_count = fact.usage_count

    # Update usage
    await service.update_fact_usage(fact.fact_id)

    # Verify
    updated_facts = await service.search_facts("Test fact")
    assert len(updated_facts) == 1
    assert updated_facts[0].usage_count == initial_count + 1
    assert updated_facts[0].last_used is not None
