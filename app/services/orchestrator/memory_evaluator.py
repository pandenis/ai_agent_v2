"""
MemoryEvaluator - Evaluates memory coverage for queries.

This component searches the memory system for relevant facts and calculates
how well the existing memory can answer the query. It's a key part of the
Intelligent Orchestrator's decision-making process.

Features:
- Search facts by topics and entities
- Calculate coverage score (0-1) based on number of relevant facts:
  * 0.0: No facts found
  * 0.5: 1 fact found (low coverage)
  * 0.7: 2-4 facts found (medium coverage)
  * 0.9: 5+ facts found (high coverage)
- Relevance scoring with RelevanceScorer (v2.1)
- Identify information gaps (topics not covered by memory)
- Dependency injection support for testing
- Graceful error handling (returns 0 coverage on failures)

Usage:
    >>> from app.services.memory_service import MemoryService
    >>> memory_service = MemoryService(db)
    >>> evaluator = MemoryEvaluator(memory_service=memory_service)
    >>> result = await evaluator.evaluate(query_analysis, session_id)
    >>> print(f"Coverage: {result.coverage_score}")
    >>> print(f"Gaps: {result.gaps}")

Testing:
    >>> # Use dependency injection for testing
    >>> mock_service = AsyncMock()
    >>> evaluator = MemoryEvaluator(memory_service=mock_service)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from app.services.memory_service import MemoryService
from app.services.orchestrator.relevance_scorer import RelevanceScorer


@dataclass
class MemoryEvaluation:
    """Result of memory evaluation"""
    coverage_score: float  # 0-1, how well memory covers the query
    relevant_facts: List[dict]  # Facts found in memory
    gaps: List[str]  # Topics/entities missing from memory
    confidence: float  # 0-1, confidence in the evaluation


class MemoryEvaluator:
    """Evaluates memory coverage for queries"""

    def __init__(self, memory_service=None, relevance_scorer=None):
        """Initialize with optional MemoryService and RelevanceScorer (for testing)"""
        self.memory_service = memory_service
        self.relevance_scorer = relevance_scorer or RelevanceScorer()

    async def evaluate(
        self, query_analysis, session_id: str, subject_hint: Optional[str] = None
    ) -> MemoryEvaluation:
        """Evaluate memory coverage for a query"""
        # Build search query from topics and entities
        search_terms = query_analysis.topics + query_analysis.entities
        search_query = " ".join(search_terms[:3]) if search_terms else ""

        # Search for relevant facts
        relevant_facts = await self._search_relevant_facts(
            query_analysis, session_id, search_query, subject_hint=subject_hint
        )

        # Calculate coverage score
        coverage_score = self._calculate_coverage(
            query_analysis, relevant_facts
        )

        # Identify gaps
        gaps = self._identify_gaps(query_analysis, relevant_facts)

        # Calculate dynamic confidence based on facts quality
        evaluation_confidence = self._calculate_confidence(relevant_facts)

        return MemoryEvaluation(
            coverage_score=coverage_score,
            relevant_facts=relevant_facts,
            gaps=gaps,
            confidence=evaluation_confidence
        )

    async def _search_relevant_facts(
        self, query_analysis, session_id: str, search_query: str,
        subject_hint: Optional[str] = None,
    ) -> List[dict]:
        """Search memory for facts related to query"""
        # If no memory service provided (tests), return empty
        if not self.memory_service:
            return []

        # Search by topics and entities
        search_terms = query_analysis.topics + query_analysis.entities

        if not search_terms:
            return []

        try:
            facts = await self.memory_service.search_facts(
                query=search_query,
                min_importance=0.3,
                limit=10,
                subject=subject_hint,
            )

            # Convert SQLAlchemy models to dicts for consistent handling
            raw_facts = []
            for fact in facts:
                if hasattr(fact, 'text'):
                    # SQLAlchemy model - convert to dict
                    raw_facts.append({
                        'text': fact.text,
                        'importance': getattr(fact, 'importance', 0.5),
                        'confidence': getattr(fact, 'confidence', 0.8),
                        'tags': getattr(fact, 'tags', []),
                        'created_at': getattr(fact, 'created_at', datetime.utcnow()),
                    })
                elif isinstance(fact, dict):
                    # Already a dict - ensure created_at exists
                    if 'created_at' not in fact:
                        fact['created_at'] = datetime.utcnow()
                    raw_facts.append(fact)

            # Score facts with RelevanceScorer
            scored_facts = self._score_and_filter_facts(search_query, raw_facts)

            return scored_facts
        except Exception as e:
            # Log and return empty on failure
            import logging
            logging.getLogger(__name__).warning(f"Memory search failed: {e}")
            return []

    def _score_and_filter_facts(self, query: str, facts: List[dict]) -> List[dict]:
        """Score and filter facts using RelevanceScorer"""
        if not facts:
            return []

        # Use default min_score of 0.3 (deep_reasoning level - most inclusive)
        scored_facts = self.relevance_scorer.score_and_filter(
            query=query,
            facts=facts,
            min_score=0.3
        )

        return scored_facts

    def _calculate_coverage(self, query_analysis, relevant_facts: List[dict]) -> float:
        """Calculate how well memory covers the query (0-1)

        Coverage is based on:
        1. Number of facts found
        2. Importance/confidence of facts (quality bonus)
        """
        if not relevant_facts:
            return 0.0

        num_facts = len(relevant_facts)

        # Base coverage from fact count
        if num_facts >= 5:
            base_coverage = 0.9
        elif num_facts >= 2:
            base_coverage = 0.7
        else:  # num_facts >= 1 (guaranteed since we returned early if empty)
            base_coverage = 0.5

        # Quality bonus: high importance/confidence facts boost coverage
        avg_importance = sum(
            fact.get('importance', 0.5) for fact in relevant_facts
        ) / num_facts

        avg_confidence = sum(
            fact.get('confidence', 0.5) for fact in relevant_facts
        ) / num_facts

        # Quality score (0-1)
        quality_score = (avg_importance + avg_confidence) / 2

        # Bonus: up to +0.2 for high quality facts
        quality_bonus = quality_score * 0.25

        # Final coverage (capped at 1.0)
        final_coverage = min(1.0, base_coverage + quality_bonus)

        return round(final_coverage, 2)

    def _identify_gaps(self, query_analysis, relevant_facts: List[dict]) -> List[str]:
        """Identify what's missing from memory (topics and entities)"""
        gaps = []

        # Combine all fact texts for searching
        all_facts_text = " ".join(
            str(fact.get('text', '')).lower() for fact in relevant_facts
        )

        # Check if we have facts for each topic
        for topic in query_analysis.topics:
            if topic.lower() not in all_facts_text:
                gaps.append(topic)

        # Check if we have facts for each entity
        for entity in query_analysis.entities:
            # Skip common/generic entities
            if entity.lower() in ['i', 'my', 'me', 'the', 'a', 'an']:
                continue
            if entity.lower() not in all_facts_text:
                gaps.append(entity)

        return gaps

    def _calculate_confidence(self, relevant_facts: List[dict]) -> float:
        """Calculate confidence in the evaluation based on fact quality

        Confidence is based on:
        - Number of facts found
        - Average importance/confidence of facts
        """
        if not relevant_facts:
            return 0.3  # Low confidence when no facts

        num_facts = len(relevant_facts)

        # Average quality of facts
        avg_importance = sum(
            fact.get('importance', 0.5) for fact in relevant_facts
        ) / num_facts

        avg_fact_confidence = sum(
            fact.get('confidence', 0.5) for fact in relevant_facts
        ) / num_facts

        # Quality score (0-1)
        quality_score = (avg_importance + avg_fact_confidence) / 2

        # Base confidence from fact count
        if num_facts >= 5:
            base_confidence = 0.7
        elif num_facts >= 2:
            base_confidence = 0.6
        else:
            base_confidence = 0.4

        # Final confidence: base + quality bonus (up to +0.3)
        final_confidence = base_confidence + (quality_score * 0.3)

        # Cap at 0.95 (never 100% confident)
        return round(min(0.95, final_confidence), 2)