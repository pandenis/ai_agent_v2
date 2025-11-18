"""
Memory service for managing conversation history and facts
Extended to support Memorisator v2 (FactModel)
"""

import uuid
from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import ConversationMessage, UserFact
from app.models.memory_v2 import Fact, FactModel

# Security import
from security.input_validation import SecurityValidator, validate_input


class MemoryService:
    """Service for managing conversation memory and user facts"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================
    # Conversation Messages
    # ========================

    async def add_message(
        self, session_id: str, role: str, content: str, tokens_used: Optional[int] = None
    ) -> ConversationMessage:
        """Add a message to conversation history"""

        # Security: Validate session_id
        is_valid_session, session_error = SecurityValidator.validate_session_id(session_id)
        if not is_valid_session:
            logger.warning(f"Invalid session_id attempted: {session_id}")
            raise ValueError(f"Invalid session ID: {session_error}")

        # Security: Validate message content
        is_valid, sanitized_content, error = validate_input(content)
        if not is_valid:
            logger.warning(f"Invalid message content blocked: {error}")
            raise ValueError(f"Invalid message content: {error}")

        message = ConversationMessage(
            session_id=session_id, role=role, content=sanitized_content, tokens_used=tokens_used  # ← Use sanitized version!
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[ConversationMessage]:
        """Get recent conversation history"""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.timestamp.desc())
            .limit(limit)
        )

        messages = result.scalars().all()
        return list(reversed(messages))  # Return in chronological order

    # ========================
    # OLD Facts (UserFact) - Legacy support
    # ========================

    async def add_fact(
        self, text: str, importance: float = 0.5, tags: Optional[List[str]] = None, source: str = "conversation"
    ) -> UserFact:
        """Add a new user fact (legacy)"""
        fact = UserFact(fact_id=str(uuid.uuid4()), text=text, importance=importance, tags=tags or [], source=source)

        self.db.add(fact)
        await self.db.commit()
        await self.db.refresh(fact)

        return fact

    async def get_important_facts(self, min_importance: float = 0.5, limit: int = 10) -> List[UserFact]:
        """Get important facts above threshold (legacy)"""
        result = await self.db.execute(
            select(UserFact).where(UserFact.importance >= min_importance).order_by(UserFact.importance.desc()).limit(limit)
        )

        return result.scalars().all()

    async def search_facts(self, query: str, min_importance: float = 0.3) -> List[UserFact]:
        """Search facts by text content (legacy)"""
        result = await self.db.execute(
            select(UserFact)
            .where(and_(UserFact.text.contains(query), UserFact.importance >= min_importance))
            .order_by(UserFact.importance.desc())
        )

        return result.scalars().all()

    async def update_fact_usage(self, fact_id: str):
        """Update fact usage statistics (legacy)"""
        result = await self.db.execute(select(UserFact).where(UserFact.fact_id == fact_id))
        fact = result.scalar_one_or_none()

        if fact:
            fact.usage_count += 1
            fact.last_used = datetime.utcnow()
            await self.db.commit()

    # ========================
    # NEW Facts (FactModel) - Memorisator v2
    # ========================

    async def add_facts(self, facts: List[Fact]) -> List[FactModel]:
        """
        Add multiple facts to database (Memorisator v2)

        Args:
            facts: List of Fact dataclass objects

        Returns:
            List of saved FactModel objects
        """
        saved_facts = []

        for fact in facts:
            try:
                # Convert Fact dataclass to FactModel
                fact_model = FactModel(
                    fact_id=fact.fact_id,
                    text=fact.text,
                    importance=fact.importance,
                    confidence=fact.confidence,
                    tags=fact.tags,
                    created=fact.created,
                    updated=fact.updated,
                    last_accessed=fact.last_accessed,
                    fact_type=fact.fact_type,
                    needs_update=fact.needs_update,
                    update_frequency=fact.update_frequency,
                    source=fact.source,
                    related_fact_ids=fact.related_fact_ids,
                    context_maps=fact.context_maps,
                    meta_data=fact.meta_data,
                    usage_count=fact.usage_count,
                )

                self.db.add(fact_model)
                saved_facts.append(fact_model)

                logger.debug(f"Added fact: {fact.text[:50]}...")

            except Exception as e:
                logger.error(f"Error adding fact: {e}")
                continue

        # Commit all at once
        if saved_facts:
            await self.db.commit()

            # Refresh all
            for fact_model in saved_facts:
                await self.db.refresh(fact_model)

            logger.info(f"Saved {len(saved_facts)} facts to database")

        return saved_facts

    async def get_facts(
        self,
        min_importance: float = 0.5,
        fact_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[FactModel]:
        """
        Get facts with filters (Memorisator v2)

        Args:
            min_importance: Minimum importance threshold
            fact_type: Filter by fact type (static, event, preference, etc.)
            tags: Filter by tags (returns facts with ANY of these tags)
            limit: Maximum number of facts to return
            offset: Offset for pagination

        Returns:
            List of FactModel objects
        """
        query = select(FactModel).where(FactModel.importance >= min_importance)

        # Filter by fact_type
        if fact_type:
            query = query.where(FactModel.fact_type == fact_type)

        # Filter by tags (if fact has ANY of the specified tags)
        # Note: This is simplified - for production you might want full-text search
        if tags:
            # For SQLite JSON filtering is limited, so we'll filter in Python
            pass  # Will filter after query

        # Order by importance and apply pagination
        query = query.order_by(FactModel.importance.desc(), FactModel.updated.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        facts = result.scalars().all()

        # Filter by tags in Python (if needed)
        if tags:
            facts = [fact for fact in facts if fact.tags and any(tag in fact.tags for tag in tags)]

        return facts

    async def get_fact_by_id(self, fact_id: str) -> Optional[FactModel]:
        """
        Get a specific fact by ID (Memorisator v2)

        Args:
            fact_id: Fact ID to retrieve

        Returns:
            FactModel or None if not found
        """
        result = await self.db.execute(select(FactModel).where(FactModel.fact_id == fact_id))
        return result.scalar_one_or_none()

    async def delete_fact(self, fact_id: str) -> bool:
        """
        Delete a fact by ID (Memorisator v2)

        Args:
            fact_id: Fact ID to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(select(FactModel).where(FactModel.fact_id == fact_id))
        fact = result.scalar_one_or_none()

        if fact:
            await self.db.delete(fact)
            await self.db.commit()
            logger.info(f"Deleted fact: {fact_id}")
            return True

        logger.warning(f"Fact not found for deletion: {fact_id}")
        return False

    async def update_fact_access(self, fact_id: str):
        """
        Update fact last_accessed and usage_count (Memorisator v2)

        Args:
            fact_id: Fact ID to update
        """
        result = await self.db.execute(select(FactModel).where(FactModel.fact_id == fact_id))
        fact = result.scalar_one_or_none()

        if fact:
            fact.usage_count += 1
            fact.last_accessed = datetime.utcnow()
            await self.db.commit()
            logger.debug(f"Updated access for fact: {fact_id}")

    async def get_facts_stats(self) -> dict:
        """
        Get statistics about facts (Memorisator v2)

        Returns:
            Dictionary with stats
        """
        # Total facts
        result = await self.db.execute(select(FactModel))
        all_facts = result.scalars().all()

        total = len(all_facts)

        # Count by type
        by_type = {}
        for fact in all_facts:
            fact_type = fact.fact_type or "unknown"
            by_type[fact_type] = by_type.get(fact_type, 0) + 1

        # Average importance
        avg_importance = sum(f.importance for f in all_facts) / total if total > 0 else 0.0

        return {"total_facts": total, "facts_by_type": by_type, "avg_importance": round(avg_importance, 2)}
