"""
Enhanced chat service with intelligent context retrieval
"""
from typing import List, Dict, Optional
from app.services.memory_service import MemoryService
from app.services.agent_service import AgentService
from app.services.document_service import DocumentService
from app.services.web_search_service import WebSearchService


class EnhancedChatService:
    """Service for intelligent multi-source chat"""
    
    def __init__(
        self,
        memory_service: MemoryService,
        agent_service: AgentService,
        document_service: DocumentService,
        web_search_service: WebSearchService
    ):
        self.memory_service = memory_service
        self.agent_service = agent_service
        self.document_service = document_service
        self.web_search_service = web_search_service
    
    def _should_search_documents(self, message: str) -> bool:
        """Determine if document search is needed"""
        message_lower = message.lower()
        
        doc_keywords = [
            # English
            "document", "file", "uploaded", "wrote", "saved",
            "in my notes", "previously", "earlier",
            # Russian
            "документ", "файл", "писал", "написал", "сохранил",
            "в моих заметках", "ранее", "раньше", "загрузил",
            # Chinese
            "文档", "文件", "记得"
        ]
        
        return any(keyword in message_lower for keyword in doc_keywords)
    
    def _should_search_web(self, message: str) -> bool:
        """Determine if web search is needed"""
        message_lower = message.lower()
        
        web_keywords = [
            # English
            "latest", "current", "recent", "today", "now",
            "news", "weather", "price", "stock", "update",
            "2024", "2025", "this year", "this month",
            # Russian
            "последн", "текущ", "сегодня", "сейчас", "новост",
            "погода", "цена", "обновл", "этом году", "этом месяце"
        ]
        
        question_words = [
            # English
            "what is", "who is", "when", "where", "how",
            # Russian
            "что такое", "кто такой", "когда", "где", "как"
        ]
        
        has_web_keyword = any(keyword in message_lower for keyword in web_keywords)
        has_question = any(q in message_lower for q in question_words)
        
        return has_web_keyword or (has_question and len(message.split()) > 3)
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        include_memory: bool = True
    ) -> Dict:
        """
        Process message with intelligent context retrieval
        
        Returns:
            Dict with response, sources, and metadata
        """
        context_parts = []
        sources_used = []
        
        # 1. Get conversation history
        conversation_history = []
        if include_memory:
            recent_messages = await self.memory_service.get_conversation_history(
                session_id, limit=5
            )
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in recent_messages
            ]
            
            if conversation_history:
                context_parts.append("Recent conversation context available.")
                sources_used.append("conversation_history")
        
        # 2. Get user facts from memory
        if include_memory:
            important_facts = await self.memory_service.get_important_facts(
                min_importance=0.6, limit=5
            )
            
            if important_facts:
                facts_text = "\n".join([f"- {f.text}" for f in important_facts])
                context_parts.append(f"Known facts about the user:\n{facts_text}")
                sources_used.append("user_facts")
        
        # 3. Search documents if relevant
        should_search_docs = self._should_search_documents(message)
        if should_search_docs:
            doc_results = await self.document_service.search_documents(
                message, n_results=3
            )
            
            if doc_results:
                docs_text = "\n\n".join([
                    f"Document: {r['metadata'].get('filename', 'Unknown')}\n{r['text'][:300]}..."
                    for r in doc_results
                ])
                context_parts.append(f"Relevant documents:\n{docs_text}")
                sources_used.append("documents")
        
        # 4. Search web if needed
        should_search_web = self._should_search_web(message)
        if should_search_web:
            web_results = await self.web_search_service.search(
                message, max_results=3
            )
            
            if web_results and "error" not in web_results[0]:
                web_text = "\n\n".join([
                    f"{r['title']}\n{r['snippet']}\nSource: {r['url']}"
                    for r in web_results[:3]
                ])
                context_parts.append(f"Web search results:\n{web_text}")
                sources_used.append("web_search")
        
        # 5. Build enhanced system prompt
        system_prompt = "You are a helpful AI assistant."
        
        if context_parts:
            system_prompt += "\n\nYou have access to the following context:\n\n"
            system_prompt += "\n\n---\n\n".join(context_parts)
            system_prompt += "\n\n---\n\n"
            system_prompt += "Use this context to provide accurate, well-sourced answers. "
            system_prompt += "When citing information, mention the source (e.g., 'According to the document...', 'Based on recent web search...')."
        
        # 6. Generate AI response
        ai_result = await self.agent_service.generate_response(
            prompt=message,
            system_prompt=system_prompt,
            conversation_history=conversation_history
        )
        
        # 7. Return enhanced response
        return {
            "response": ai_result["response"],
            "status": ai_result["status"],
            "sources_used": sources_used,
            "tokens": ai_result.get("tokens", 0),
            "model": ai_result.get("model", "unknown")
        }
