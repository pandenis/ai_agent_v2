"""QueryAnalyzer - analyzes user queries for complexity and intent"""
from dataclasses import dataclass
from typing import List


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    complexity: str  # "simple", "medium", "complex"
    intent: str  # "question", "command", "statement"
    query_type: str  # "factual", "reasoning", "creative"
    entities: List[str]  # Extracted entities
    topics: List[str]  # Main topics
    requires_memory: bool
    requires_reasoning: bool
    confidence: float  # 0-1


class QueryAnalyzer:
    """Analyzes query complexity, intent, and entities"""

    # Patterns for complex queries
    COMPLEX_PATTERNS = [
        "compare",
        "analyze",
        "evaluate",
        "assess",
    ]

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a query and return analysis results"""
        query_lower = query.lower()

        # Detect complexity
        complexity = self._detect_complexity(query_lower)
        requires_reasoning = (complexity == "complex")

        return QueryAnalysis(
            complexity=complexity,
            intent="question",
            query_type="factual",
            entities=[],
            topics=[],
            requires_memory=True,
            requires_reasoning=requires_reasoning,
            confidence=1.0
        )

    def _detect_complexity(self, query_lower: str) -> str:
        """Detect query complexity based on patterns"""
        # Check for complex patterns
        for pattern in self.COMPLEX_PATTERNS:
            if pattern in query_lower:
                return "complex"

        # Default to simple
        return "simple"