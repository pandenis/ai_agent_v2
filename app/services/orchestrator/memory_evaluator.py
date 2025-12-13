"""
MemoryEvaluator - Evaluates memory coverage for queries.

This component searches the memory system for relevant facts and calculates
how well the existing memory can answer the query.

Features:
- Search facts by topics and entities
- Calculate coverage score (0-1)
- Identify information gaps
- Recommend memory-based vs AI-based responses

Example:
    >>> evaluator = MemoryEvaluator()
    >>> result = await evaluator.evaluate(query_analysis, session_id)
    >>> print(result.coverage_score)  # 0.8
"""
from dataclasses import dataclass
from typing import List, Optional
from app.services.memory_service import MemoryService


@dataclass
class MemoryEvaluation:
    """Result of memory evaluation"""
    coverage_score: float  # 0-1, how well memory covers the query
    relevant_facts: List[dict]  # Facts found in memory
    gaps: List[str]  # Topics/entities missing from memory
    confidence: float  # 0-1, confidence in the evaluation


class MemoryEvaluator:
    """Evaluates memory coverage for queries"""

    def __init__(self, memory_service=None):
        """Initialize with optional MemoryService (for testing)"""
        self.memory_service = memory_service

    async def evaluate(self, query_analysis, session_id: str) -> MemoryEvaluation:
        """Evaluate memory coverage for a query"""
        # Search for relevant facts
        relevant_facts = await self._search_relevant_facts(
            query_analysis, session_id
        )

        # Calculate coverage score
        coverage_score = self._calculate_coverage(
            query_analysis, relevant_facts
        )

        # Identify gaps
        gaps = self._identify_gaps(query_analysis, relevant_facts)

        return MemoryEvaluation(
            coverage_score=coverage_score,
            relevant_facts=relevant_facts,
            gaps=gaps,
            confidence=0.8  # High confidence in evaluation
        )

    async def _search_relevant_facts(self, query_analysis, session_id: str) -> List[dict]:
        """Search memory for facts related to query"""
        # If no memory service provided (tests), return empty
        if not self.memory_service:
            return []

        # Search by topics and entities
        search_terms = query_analysis.topics + query_analysis.entities

        if not search_terms:
            return []

        # Use first topic/entity as search query
        search_query = " ".join(search_terms[:3])  # Top 3 terms

        try:
            facts = await self.memory_service.search_facts(
                query=search_query,
                session_id=session_id,
                limit=10
            )
            return facts if facts else []
        except Exception:
            # If memory service fails, return empty
            return []

    def _calculate_coverage(self, query_analysis, relevant_facts: List[dict]) -> float:
        """Calculate how well memory covers the query (0-1)"""
        if not relevant_facts:
            return 0.0

        # Simple coverage based on number of facts found
        num_facts = len(relevant_facts)

        # More facts = better coverage
        if num_facts >= 5:
            return 0.9
        elif num_facts >= 2:
            return 0.7
        elif num_facts >= 1:
            return 0.5
        else:
            return 0.0

    def _identify_gaps(self, query_analysis, relevant_facts: List[dict]) -> List[str]:
        """Identify what's missing from memory"""
        gaps = []

        # Check if we have facts for each topic
        for topic in query_analysis.topics:
            has_topic_facts = any(
                topic.lower() in str(fact.get('text', '')).lower()
                for fact in relevant_facts
            )
            if not has_topic_facts:
                gaps.append(topic)

        return gaps