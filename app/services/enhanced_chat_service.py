"""
Enhanced chat service with multi-source intelligence and agent selection
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_service import AgentService
from app.services.memory_service import MemoryService
from app.services.document_service import DocumentService
from app.services.web_search_service import WebSearchService
from app.core.agent_config import TaskType


class EnhancedChatService:
    """
    Enhanced chat service with:
    - Multi-source context retrieval
    - Intelligent agent selection
    - Source tracking
    """
    
    # Keywords that trigger document search
    DOCUMENT_KEYWORDS = [
        "document", "file", "wrote", "write", "писал", "документ", 
        "uploaded", "saved", "записал", "сохранил"
    ]
    
    # Keywords that trigger web search
    WEB_KEYWORDS = [
        "latest", "current", "news", "today", "2025",
        "последние", "новости", "сегодня", "актуальное"
    ]
    
    def __init__(
        self,
        agent_service: AgentService,
        memory_service: MemoryService,
        document_service: DocumentService,
        web_search_service: WebSearchService
    ):
        self.agent_service = agent_service
        self.memory_service = memory_service
        self.document_service = document_service
        self.web_search_service = web_search_service
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        agent_name: Optional[str] = None,  # NEW: Agent selection
        include_memory: bool = True,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Process message with multi-source intelligence and agent selection
        
        Args:
            session_id: Chat session ID
            message: User message
            agent_name: Specific agent (or None for auto-select)  # NEW
            include_memory: Include conversation history
            db: Database session
            
        Returns:
            Dict with response, agent used, sources, etc.
        """
        sources = []
        context_parts = []
        
        # 1. Check if we should search documents
        if self._should_search_documents(message):
            doc_results = await self.document_service.search_documents(
                query=message,
                n_results=3
            )
            if doc_results:
                sources.append("documents")
                context_parts.append(
                    f"Relevant documents:\n" + 
                    "\n".join([f"- {r['text'][:200]}..." for r in doc_results])
                )
        
        # 2. Check if we should search web
        if self._should_search_web(message):
            web_results = await self.web_search_service.search(
                query=message,
                max_results=3
            )
            if web_results:
                sources.append("web_search")
                context_parts.append(
                    f"Web search results:\n" +
                    "\n".join([f"- {r['title']}: {r['snippet']}" for r in web_results])
                )
        
        # 3. Get conversation history and facts
        if include_memory:
            sources.append("conversation_history")
            
            # Get recent conversation
            history = await self.memory_service.get_conversation_history(
                session_id=session_id,
                limit=5
            )
            if history:
                context_parts.append(
                    f"Recent conversation:\n" +
                    "\n".join([f"{m['role']}: {m['content'][:100]}..." for m in history])
                )
            
            # Get relevant facts
            facts = await self.memory_service.search_facts(
                query=message,
                limit=3
            )
            if facts:
                sources.append("user_facts")
                context_parts.append(
                    f"Relevant facts:\n" +
                    "\n".join([f"- {f['text']}" for f in facts])
                )
        
        # 4. Build enhanced prompt with context
        enhanced_prompt = message
        if context_parts:
            enhanced_prompt = (
                f"Context:\n{chr(10).join(context_parts)}\n\n"
                f"User question: {message}"
            )
        
        # 5. NEW: Auto-select agent if not specified
        if not agent_name:
            # Infer task type from keywords
            task_type = self._infer_task_type(message)
            agent_name = await self.agent_service.select_best_agent_for_task(
                message,
                task_type=task_type
            )
        
        # 6. Generate response using selected agent
        result = await self.agent_service.generate_response(
            prompt=enhanced_prompt,
            agent_name=agent_name  # NEW: Pass selected agent
        )
        
        # 7. Add source attribution to response
        response_text = result.get("response", "")
        if sources:
            response_text += f"\n\n[Sources: {', '.join(sources)}]"
        
        # 8. Save to memory if db provided
        if db and include_memory:
            await self.memory_service.add_message(
                session_id=session_id,
                role="user",
                content=message,
                db=db
            )
            await self.memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=response_text,
                db=db
            )
        
        # 9. NEW: Return with agent info
        return {
            "response": response_text,
            "agent_used": agent_name,  # NEW
            "sources": sources,  # NEW
            "tokens": result.get("tokens", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _should_search_documents(self, message: str) -> bool:
        """Check if message should trigger document search"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.DOCUMENT_KEYWORDS)
    
    def _should_search_web(self, message: str) -> bool:
        """Check if message should trigger web search"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.WEB_KEYWORDS)
    
    def _infer_task_type(self, message: str) -> Optional[TaskType]:
        """
        NEW METHOD: Infer task type from message keywords
        
        In future, this could use ML classification
        """
        message_lower = message.lower()
        
        # Code-related keywords
        if any(word in message_lower for word in [
            "code", "python", "javascript", "function", "class",
            "bug", "error", "программ", "код", "функция"
        ]):
            return TaskType.CODE_ANALYSIS
        
        # Medical keywords
        if any(word in message_lower for word in [
            "health", "medical", "symptom", "doctor", "medicine",
            "здоровье", "симптом", "лекарство"
        ]):
            return TaskType.MEDICAL_QUERY
        
        # Creative writing
        if any(word in message_lower for word in [
            "write", "story", "poem", "creative", "напиши", "история"
        ]):
            return TaskType.CREATIVE_WRITING
        
        # Default to general chat
        return TaskType.GENERAL_CHAT
