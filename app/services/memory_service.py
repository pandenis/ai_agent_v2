"""
Memory service for managing conversation history and facts
Extended to support Memorisator v2 (FactModel)
"""
import re
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

        # Security: Validate message content (ONLY for user messages)
        if role == "user":
            is_valid, sanitized_content, error = validate_input(content)
            if not is_valid:
                logger.warning(f"Invalid message content blocked: {error}")
                raise ValueError(f"Invalid message content: {error}")
        else:
            # Don't sanitize AI responses - they need to contain code, symbols, etc.
            sanitized_content = content

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

    async def get_important_facts(self, min_importance: float = 0.5, limit: int = 10) -> List[FactModel]:
        """Get important facts above threshold (Memorisator v2)"""
        result = await self.db.execute(
            select(FactModel)
            .where(FactModel.importance >= min_importance)
            .order_by(FactModel.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_facts(
            self,
            query: str,
            min_importance: float = 0.3,
            limit: int = 10,
            thread_id: Optional[str] = None,
    ) -> List[FactModel]:
        """
        Search facts by text query with thread isolation (Memorisator v2)

        Args:
            query: Search text
            min_importance: Minimum importance threshold (default 0.3)
            limit: Maximum number of results (default 10)
            thread_id: Thread/session ID for isolation. Only facts with matching
                       thread_id are returned. None returns only global facts.

        Returns:
            List of matching FactModel objects filtered by thread_id
        """
        # Build query with thread isolation
        result = await self.db.execute(
            select(FactModel)
            .where(
                and_(
                    FactModel.text.contains(query),
                    FactModel.importance >= min_importance,
                    FactModel.thread_id == thread_id  # NEW: Thread isolation!
                )
            )
            .order_by(FactModel.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear_thread_facts(self, thread_id: Optional[str]) -> int:
        """
        Delete all facts for a specific thread (session reset).

        Used when user resets/deletes a session to clear all thread-specific memory.
        Facts in other threads are NOT affected.

        Args:
            thread_id: Thread ID to clear. Use None to clear global facts only.

        Returns:
            Number of facts deleted
        """
        # Find all facts for this thread
        result = await self.db.execute(
            select(FactModel).where(FactModel.thread_id == thread_id)
        )
        facts_to_delete = list(result.scalars().all())

        deleted_count = len(facts_to_delete)

        # Delete each fact
        for fact in facts_to_delete:
            await self.db.delete(fact)

        # Commit if we deleted anything
        if deleted_count > 0:
            await self.db.commit()
            logger.info(f"Cleared {deleted_count} facts for thread: {thread_id}")

        return deleted_count

    async def update_fact_usage(self, fact_id: str):
        """Update fact usage statistics (Memorisator v2)"""
        result = await self.db.execute(
            select(FactModel).where(FactModel.fact_id == fact_id)
        )
        fact = result.scalar_one_or_none()
        if fact:
            fact.usage_count += 1
            fact.last_accessed = datetime.utcnow()
            await self.db.commit()

    # ========================
    # NEW Facts (FactModel) - Memorisator v2
    # ========================

    async def add_facts(self, facts: List[Fact]) -> List[FactModel]:
        """
        Add multiple facts to database with duplicate prevention.

        Args:
            facts: List of Fact dataclass objects

        Returns:
            List of saved FactModel objects (excludes duplicates)
        """
        saved_facts = []

        # Get existing facts for duplicate check
        existing_facts = await self.get_facts()
        existing_texts = [f.text for f in existing_facts]

        for fact in facts:
            try:
                # Check for duplicates
                is_duplicate = False
                for existing_text in existing_texts:
                    similarity = self._calculate_similarity(fact.text, existing_text)
                    if similarity >= 0.70:
                        logger.debug(
                            f"Skipping duplicate fact: '{fact.text[:50]}...' "
                            f"(similarity {similarity:.2f} with existing)"
                        )
                        is_duplicate = True
                        break

                if is_duplicate:
                    continue

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
                    source_session_id=fact.source_session_id,
                    thread_id=fact.thread_id,
                    related_fact_ids=fact.related_fact_ids,
                    context_maps=fact.context_maps,
                    meta_data=fact.meta_data,
                    usage_count=fact.usage_count,
                )

                self.db.add(fact_model)
                saved_facts.append(fact_model)

                # Also add to existing_texts to prevent duplicates within same batch
                existing_texts.append(fact.text)

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

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0.0-1.0
        """
        import re  # Or add to imports at top of file

        # Normalize: lowercase and remove punctuation
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())

        # Tokenize
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

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

    async def update_fact(
            self,
            fact_id: str,
            tags: Optional[List[str]] = None,
            usage_count: Optional[int] = None,
            importance: Optional[float] = None,
            confidence: Optional[float] = None,
            needs_update: Optional[bool] = None,
    ) -> bool:
        """
        Update specific fields of a fact (Memorisator v2)

        Used by MemoryAuditor for merging duplicate facts.

        Args:
            fact_id: Fact ID to update
            tags: New tags list (replaces existing)
            usage_count: New usage count
            importance: New importance score
            confidence: New confidence score
            needs_update: Whether fact needs update

        Returns:
            True if updated, False if not found
        """
        result = await self.db.execute(
            select(FactModel).where(FactModel.fact_id == fact_id)
        )
        fact = result.scalar_one_or_none()

        if not fact:
            logger.warning(f"Fact not found for update: {fact_id}")
            return False

        # Update only provided fields
        if tags is not None:
            fact.tags = tags
        if usage_count is not None:
            fact.usage_count = usage_count
        if importance is not None:
            fact.importance = importance
        if confidence is not None:
            fact.confidence = confidence
        if needs_update is not None:
            fact.needs_update = needs_update

        fact.updated = datetime.utcnow()

        await self.db.commit()
        logger.info(f"Updated fact: {fact_id}")
        return True

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
