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

        # Extract topics
        topics = self._identify_topics(query_lower, entities)

        # Detect intent
        intent = self._detect_intent(query_lower)

        # Detect query type
        query_type = self._detect_query_type(query_lower)

        return QueryAnalysis(
            complexity=complexity,
            intent=intent,
            query_type=query_type,
            entities=entities,
            topics=topics,
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

    def _identify_topics(self, query_lower: str, entities: List[str]) -> List[str]:
        """Identify main topics based on keywords and entities"""
        topics = []

        # Programming indicators
        programming_keywords = ['python', 'code', 'bug', 'function', 'database',
                                'programming', 'javascript', 'java', 'api']
        if any(keyword in query_lower for keyword in programming_keywords):
            topics.append("programming")

        # Medical indicators
        medical_keywords = ['symptom', 'disease', 'treatment', 'medicine',
                            'diagnosis', 'doctor', 'health', 'medical']
        if any(keyword in query_lower for keyword in medical_keywords):
            topics.append("medical")

        # Creative indicators
        creative_keywords = ['story', 'write', 'creative', 'poem', 'article', 'blog']
        if any(keyword in query_lower for keyword in creative_keywords):
            topics.append("creative")

        # Analysis indicators
        analysis_keywords = ['analyze', 'compare', 'evaluate', 'assess', 'review']
        if any(keyword in query_lower for keyword in analysis_keywords):
            topics.append("analysis")

        # General if no specific topic found
        if not topics:
            topics.append("general")

        return topics

    def _detect_intent(self, query_lower: str) -> str:
        """Detect query intent: question, command, or statement"""
        # Command patterns (imperative verbs)
        command_patterns = [
            'create', 'make', 'write', 'generate', 'build',
            'translate', 'convert', 'transform', 'calculate',
            'find', 'search', 'show', 'display', 'list',
            'explain', 'describe', 'tell me', 'give me'
        ]

        # Check for commands (starts with imperative verb)
        first_word = query_lower.split()[0] if query_lower.split() else ""
        if first_word in command_patterns:
            return "command"

        # Check for any command pattern in query
        if any(pattern in query_lower for pattern in command_patterns):
            return "command"

        # Question patterns
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose']
        if any(query_lower.startswith(word) for word in question_words):
            return "question"

        # Question mark
        if '?' in query_lower:
            return "question"

        # Default to statement
        return "statement"

    def _detect_query_type(self, query_lower: str) -> str:
        """Detect query type: factual, reasoning, or creative"""
        # Creative patterns
        creative_patterns = [
            'write', 'create', 'compose', 'draft',
            'poem', 'story', 'essay', 'article',
            'imagine', 'design', 'invent'
        ]

        if any(pattern in query_lower for pattern in creative_patterns):
            return "creative"

        # Reasoning patterns (why, how come, explain why)
        reasoning_patterns = [
            'why ', 'why?',
            'how come',
            'explain why',
            'what causes',
            'what is the reason'
        ]

        if any(pattern in query_lower for pattern in reasoning_patterns):
            return "reasoning"

        # Default to factual
        return "factual"