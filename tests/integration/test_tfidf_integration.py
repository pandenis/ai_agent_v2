"""
Integration tests verifying TF-IDF flows through the full pipeline.

These tests use real TfidfSimilarity (no mocks) to confirm:
1. MemoryMap.build_context_for_query() scores nodes via TF-IDF
2. RelevanceScorer.text_similarity() differentiates relevant vs irrelevant facts

No running server required — pure Python integration.
"""

from datetime import datetime

from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode
from app.services.orchestrator.relevance_scorer import RelevanceScorer


class TestTfidfIntegration:

    def test_orchestrator_context_uses_tfidf_scoring(self):
        """Verify TF-IDF is active in MemoryMap → build_context_for_query pipeline.

        Pipeline: query → TfidfSimilarity.calculate(query, [node contents])
                  → combined score (0.5*tfidf + 0.5*weight) → seed selection
                  → build_local_slice → to_prompt_context → result string

        The diabetes node shares the word "diabetes" with the query, giving it
        a high TF-IDF score. The pasta and Berlin nodes share no distinctive
        words with the query and should score lower.
        """
        # Arrange
        now = datetime.utcnow()
        memory_map = MemoryMap()
        node_diabetes = MemoryNode(
            id="n1",
            content="User was diagnosed with type 2 diabetes in 2023",
            node_type="fact",
            importance=0.8,
            last_accessed=now,
        )
        node_pasta = MemoryNode(
            id="n2",
            content="User enjoys cooking Italian pasta dishes",
            node_type="fact",
            importance=0.8,
            last_accessed=now,
        )
        node_berlin = MemoryNode(
            id="n3",
            content="User lives in Berlin and speaks German",
            node_type="fact",
            importance=0.8,
            last_accessed=now,
        )
        for node in [node_diabetes, node_pasta, node_berlin]:
            memory_map.add_node(node)

        # Act
        result = memory_map.build_context_for_query(
            "diabetes treatment options", token_budget=500
        )

        # Assert — diabetes node appears in the context
        assert "diabetes" in result

        # Verify via retrieval log that diabetes node scored higher than pasta
        log = memory_map.last_retrieval_log
        scores = {nid: score for nid, score in log.top_scores}
        # n1 (diabetes) should be present and scored
        assert "n1" in scores

        # If both are scored, diabetes should rank above pasta/Berlin
        if "n2" in scores:
            assert scores["n1"] > scores["n2"]
        if "n3" in scores:
            assert scores["n1"] > scores["n3"]

    def test_tfidf_scoring_end_to_end_with_relevance_scorer(self):
        """Verify RelevanceScorer.text_similarity uses TF-IDF to differentiate facts.

        Pipeline: query → RelevanceScorer.text_similarity(query, fact_text)
                  → TfidfSimilarity.calculate(query, [fact_text])
                  → cosine similarity score

        Fact A shares "weather" with the query → positive TF-IDF score.
        Fact B has zero word overlap with the query → zero TF-IDF score.
        """
        # Arrange
        scorer = RelevanceScorer()
        query = "weather forecast for tomorrow"
        fact_a = "The weather in Berlin is currently 15 degrees and cloudy"
        fact_b = "User's favorite color is blue"

        # Act
        score_a = scorer.text_similarity(query, fact_a)
        score_b = scorer.text_similarity(query, fact_b)

        # Assert — Fact A (weather) scores significantly higher than Fact B (color)
        assert score_a > 0.0
        assert score_a >= score_b * 2
