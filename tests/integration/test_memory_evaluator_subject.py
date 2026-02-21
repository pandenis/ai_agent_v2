"""
Integration tests: MemoryEvaluator subject_hint wiring (MEM-002-05, step 13 of 13).

Verifies that:
1. MemoryEvaluator.evaluate() passes subject_hint to search_facts() as the
   subject= kwarg, enabling subject-filtered memory retrieval.
2. A DecisionEngine receiving high-coverage evaluation from a covered
   technical query selects the 'direct' strategy.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.memory_v2 import Fact
from app.services.orchestrator.decision_engine import DecisionEngine
from app.services.orchestrator.memory_evaluator import MemoryEvaluation, MemoryEvaluator


def _make_technology_facts(n: int = 5) -> list:
    """Return n Fact objects with subject='technology' and importance=0.9."""
    texts = [
        "FastAPI uses Python asyncio for async handling",
        "FastAPI supports async def route handlers natively",
        "FastAPI leverages asyncio event loop under the hood",
        "FastAPI async programming improves API throughput",
        "FastAPI integrates with asyncio-compatible libraries",
    ]
    return [
        Fact(
            fact_id=f"f{i}",
            text=texts[i % len(texts)],
            subject="technology",
            importance=0.9,
            thread_id="t1",
        )
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_evaluator_passes_subject_hint_to_search_facts():
    """
    Verifies that MemoryEvaluator.evaluate() calls memory_service.search_facts()
    with subject='technology' when subject_hint='technology' is passed, and that
    the returned coverage score reflects the 5 high-importance facts found.

    Ensures the subject hint propagates from evaluate() → _search_relevant_facts()
    → search_facts(subject=...) without being silently dropped.
    """
    # Arrange
    memory_service = MagicMock()
    memory_service.search_facts = AsyncMock(return_value=_make_technology_facts(5))

    evaluator = MemoryEvaluator(memory_service=memory_service)

    query_analysis = MagicMock()
    query_analysis.topics = ["programming"]
    query_analysis.entities = ["FastAPI"]

    # Act
    result = await evaluator.evaluate(
        query_analysis=query_analysis,
        session_id="t1",
        subject_hint="technology",
    )

    # Assert — search_facts called exactly once with subject='technology'
    memory_service.search_facts.assert_called_once()
    call_kwargs = memory_service.search_facts.call_args.kwargs
    assert call_kwargs.get("subject") == "technology", (
        f"Expected subject='technology' in search_facts kwargs, got: {call_kwargs}"
    )

    # Assert — 5 high-importance facts yield coverage >= 0.9
    assert result.coverage_score >= 0.9, (
        f"Expected coverage >= 0.9 for 5 high-importance facts, got {result.coverage_score}"
    )


def test_direct_strategy_for_covered_technical_query():
    """
    Verifies that DecisionEngine selects 'direct' strategy when MemoryEvaluation
    reports coverage=0.95 for a simple technical query.

    This confirms that subject-filtered retrieval enabling high memory coverage
    flows through to the correct strategy selection — i.e. the system can answer
    from memory alone without calling an AI model.
    """
    # Arrange — high coverage evaluation (as would come from subject-filtered retrieval)
    memory_eval = MemoryEvaluation(
        coverage_score=0.95,
        relevant_facts=[
            {"text": "FastAPI uses asyncio", "importance": 0.9, "confidence": 0.9},
        ],
        gaps=[],
        confidence=0.92,
    )

    query_analysis = MagicMock()
    query_analysis.complexity = "simple"
    query_analysis.intent = "question"
    query_analysis.topics = ["programming"]
    query_analysis.entities = ["FastAPI"]
    query_analysis.query_type = "factual"

    decision_engine = DecisionEngine()

    # Act
    strategy = decision_engine.decide(
        query_analysis=query_analysis,
        memory_eval=memory_eval,
    )

    # Assert — coverage >= 0.9 + simple complexity → direct strategy
    assert strategy.strategy == "direct", (
        f"Expected 'direct' strategy for coverage=0.95 + simple query, "
        f"got '{strategy.strategy}'"
    )
