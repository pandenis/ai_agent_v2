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

    # Patterns for medium queries
    MEDIUM_PATTERNS = [
        "how to",
        "how can",
        "what are the steps",
        "explain",
        "why does",
    ]

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a query and return analysis results"""
        query_lower = query.lower()

        # Detect complexity
        complexity = self._detect_complexity(query_lower)
        requires_reasoning = (complexity == "complex")

        # Extract entities
        entities = self._extract_entities(query)

        return QueryAnalysis(
            complexity=complexity,
            intent="question",
            query_type="factual",
            entities=entities,
            topics=[],
            requires_memory=True,
            requires_reasoning=requires_reasoning,
            confidence=1.0
        )

    def _detect_complexity(self, query_lower: str) -> str:
        """Detect query complexity based on patterns"""
        # Check for complex patterns first
        for pattern in self.COMPLEX_PATTERNS:
            if pattern in query_lower:
                return "complex"

        # Check for medium patterns
        for pattern in self.MEDIUM_PATTERNS:
            if pattern in query_lower:
                return "medium"

        # Default to simple
        return "simple"

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities (capitalized words and known terms)"""
        entities = []
        words = query.split()

        # Extract capitalized words (like "Python")
        for word in words:
            # Remove punctuation
            clean_word = word.strip('?.,!;:')
            # Check if starts with capital letter
            if clean_word and clean_word[0].isupper():
                entities.append(clean_word)

        # Extract known technical terms
        known_terms = [
            # Programming
            'bug', 'error', 'issue', 'code', 'function', 'database',
            # Medical
            'symptom', 'disease', 'treatment', 'medicine', 'diagnosis',
            # General
            'problem', 'solution', 'question', 'answer', 'help',
            'file', 'document', 'data', 'system', 'process'
        ]
        query_lower = query.lower()
        for term in known_terms:
            if term in query_lower and term not in [e.lower() for e in entities]:
                entities.append(term)

        return entities