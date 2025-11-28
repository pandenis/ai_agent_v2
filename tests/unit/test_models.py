"""
Unit tests for database models
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.memory import ConversationMessage, UserFact
from app.models.session import Session


@pytest.mark.asyncio
async def test_create_session(test_db, sample_session_data):
    """Test creating a new session"""
    # Create session
    session = Session(**sample_session_data)
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    # Verify
    assert session.session_id is not None
    assert session.session_id == sample_session_data["session_id"]
    assert session.agent_name == sample_session_data["agent_name"]
    assert session.is_active is True
    assert session.message_count == 0
    assert isinstance(session.created_at, datetime)


@pytest.mark.asyncio
async def test_create_user_fact(test_db, sample_fact_data):
    """Test creating a user fact"""
    # Create fact
    fact = UserFact(**sample_fact_data)
    test_db.add(fact)
    await test_db.commit()
    await test_db.refresh(fact)

    # Verify
    assert fact.id is not None
    assert fact.text == sample_fact_data["text"]
    assert fact.importance == sample_fact_data["importance"]
    assert fact.tags == sample_fact_data["tags"]
    assert fact.usage_count == 0


@pytest.mark.asyncio
async def test_create_conversation_message(test_db):
    """Test creating a conversation message"""
    # Create message
    message = ConversationMessage(session_id="test-session-123", role="user", content="Hello, AI!")
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)

    # Verify
    assert message.id is not None
    assert message.role == "user"
    assert message.content == "Hello, AI!"
    assert isinstance(message.timestamp, datetime)


@pytest.mark.asyncio
async def test_query_facts_by_importance(test_db):
    """Test querying facts by importance"""
    # Create multiple facts
    facts = [UserFact(fact_id=f"fact-{i}", text=f"Fact {i}", importance=i * 0.1) for i in range(1, 11)]

    for fact in facts:
        test_db.add(fact)
    await test_db.commit()

    # Query facts with importance > 0.5
    result = await test_db.execute(select(UserFact).where(UserFact.importance > 0.5))
    high_importance_facts = result.scalars().all()

    # Verify
    assert len(high_importance_facts) == 5  # Facts 6-10
    assert all(f.importance > 0.5 for f in high_importance_facts)
