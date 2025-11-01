"""
Memory service for managing conversation history and facts
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory import ConversationMessage, UserFact
import uuid


class MemoryService:
    """Service for managing conversation memory and user facts"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None
    ) -> ConversationMessage:
        """Add a message to conversation history"""
        message = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """Get recent conversation history"""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.timestamp.desc())
            .limit(limit)
        )
        
        messages = result.scalars().all()
        return list(reversed(messages))  # Return in chronological order
    
    async def add_fact(
        self,
        text: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        source: str = "conversation"
    ) -> UserFact:
        """Add a new user fact"""
        fact = UserFact(
            fact_id=str(uuid.uuid4()),
            text=text,
            importance=importance,
            tags=tags or [],
            source=source
        )
        
        self.db.add(fact)
        await self.db.commit()
        await self.db.refresh(fact)
        
        return fact
    
    async def get_important_facts(
        self,
        min_importance: float = 0.5,
        limit: int = 10
    ) -> List[UserFact]:
        """Get important facts above threshold"""
        result = await self.db.execute(
            select(UserFact)
            .where(UserFact.importance >= min_importance)
            .order_by(UserFact.importance.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def search_facts(
        self,
        query: str,
        min_importance: float = 0.3
    ) -> List[UserFact]:
        """Search facts by text content"""
        result = await self.db.execute(
            select(UserFact)
            .where(
                and_(
                    UserFact.text.contains(query),
                    UserFact.importance >= min_importance
                )
            )
            .order_by(UserFact.importance.desc())
        )
        
        return result.scalars().all()
    
    async def update_fact_usage(self, fact_id: str):
        """Update fact usage statistics"""
        result = await self.db.execute(
            select(UserFact).where(UserFact.fact_id == fact_id)
        )
        fact = result.scalar_one_or_none()
        
        if fact:
            fact.usage_count += 1
            fact.last_used = datetime.utcnow()
            await self.db.commit()
