"""
QueryAnalyzer - Analyzes user queries for complexity, intent, entities, and topics.

This component is part of the Intelligent Orchestrator system and provides
the first stage of query processing. It uses pattern matching and keyword
detection to classify queries without requiring an LLM.

Features:
- Complexity detection (simple/medium/complex)
- Intent detection (question/command/statement)
- Query type classification (factual/reasoning/creative)
- Entity extraction (capitalized words + common terms)
- Topic identification (programming/medical/creative/analysis/general)
- Confidence scoring (0.3-1.0 based on query clarity)

Example:
    >>> analyzer = QueryAnalyzer()
    >>> result = analyzer.analyze("How to fix a Python bug?")
    >>> print(result.complexity)  # "medium"
    >>> print(result.topics)      # ["programming"]
    >>> print(result.entities)    # ["How", "Python", "bug"]
"""

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
    # Patterns for complex queries
    COMPLEX_PATTERNS = [
        "compare",
        "analyze",
        "evaluate",
        "assess",
        # Comparison patterns
        "pros and cons",
        "advantages and disadvantages",
        "difference between",
        "trade-off",
        "trade-offs",
        # Analysis patterns
        "implications of",
        "impact of",
        "relationship between",
    ]

    # Patterns for medium queries
    MEDIUM_PATTERNS = [
        "how to",
        "how can",
        "what are the steps",
        "explain",
        "why does",
        # Help patterns
        "help me with",
        "can you help",
        # Instructional patterns
        "best practices",
        "what should i do",
        "tell me about",
        "give me examples",
        "show me",
        # Learning patterns
        "teach me",
        "guide me",
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

        # Calculate confidence
        confidence = self._calculate_confidence(query, entities, topics)

        return QueryAnalysis(
            complexity=complexity,
            intent=intent,
            query_type=query_type,
            entities=entities,
            topics=topics,
            requires_memory=True,
            requires_reasoning=requires_reasoning,
            confidence=confidence
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
        """Extract entities (emails, URLs, capitalized words, known terms)"""
        import re

        entities = []

        # 1. Extract emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, query)
        entities.extend(emails)

        # 2. Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, query)
        entities.extend(urls)

        # 3. Extract numbers with context (e.g., "5 years", "150 kg", "$100")
        number_pattern = r'\$?\d+(?:\.\d+)?(?:\s*(?:years?|months?|days?|hours?|kg|mb|gb|tb|%|dollars?|usd|eur))?'
        numbers = re.findall(number_pattern, query.lower())
        for num in numbers:
            if num.strip() and num.strip() not in entities:
                entities.append(num.strip())

        # 4. Extract capitalized words (like "Python") - but not first word of sentence
        words = query.split()
        for i, word in enumerate(words):
            clean_word = word.strip('?.,!;:')
            # Skip if it's an email or URL (already extracted)
            if '@' in clean_word or clean_word.startswith('http'):
                continue
            # Check if starts with capital letter and not first word
            if clean_word and clean_word[0].isupper():
                # Skip common first words that aren't real entities
                if i == 0 and clean_word.lower() in ['my', 'i', 'the', 'a', 'an', 'this', 'that', 'what', 'how', 'why',
                                                     'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should',
                                                     'will', 'do', 'does', 'is', 'are', 'was', 'were', 'have', 'has',
                                                     'had', 'send', 'check', 'call', 'tell', 'give', 'show']:
                    continue
                entities.append(clean_word)

        # 5. Extract known technical terms
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

        # Personal/Identity indicators
        personal_keywords = {
            'name': ['name', 'who am i', 'call me', 'called'],
            'profession': ['profession', 'job', 'work', 'career', 'occupation', 'employed', 'company'],
            'location': ['live', 'location', 'address', 'where am i', 'city', 'country', 'home', 'moved'],
            'preference': ['favorite', 'prefer', 'like best', 'favourite', 'love', 'enjoy'],
            'age': ['age', 'old', 'born', 'birthday', 'birth date'],
            'family': ['family', 'married', 'wife', 'husband', 'children', 'kids', 'parent', 'mother', 'father',
                       'brother', 'sister', 'son', 'daughter'],
            'contact': ['email', 'phone', 'number', 'contact', 'reach'],
        }

        for topic, keywords in personal_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)

        # Programming/Technical indicators
        programming_keywords = ['python', 'code', 'bug', 'function', 'database',
                                'programming', 'javascript', 'java', 'api', 'git',
                                'sql', 'html', 'css', 'react', 'node', 'django',
                                'flask', 'fastapi', 'docker', 'kubernetes', 'linux',
                                'server', 'deploy', 'debug', 'error', 'exception',
                                'class', 'method', 'variable', 'loop', 'array', 'list']
        if any(keyword in query_lower for keyword in programming_keywords):
            topics.append("programming")

        # Medical/Health indicators
        medical_keywords = ['symptom', 'disease', 'treatment', 'medicine',
                            'diagnosis', 'doctor', 'health', 'medical', 'pain',
                            'hospital', 'clinic', 'prescription', 'vaccine',
                            'allergy', 'infection', 'therapy', 'surgery',
                            'mental health', 'anxiety', 'depression', 'diet',
                            'exercise', 'sleep', 'nutrition', 'vitamin']
        if any(keyword in query_lower for keyword in medical_keywords):
            topics.append("medical")

        # Creative/Writing indicators
        creative_keywords = ['story', 'write', 'creative', 'poem', 'article', 'blog',
                             'essay', 'novel', 'fiction', 'script', 'content',
                             'draft', 'edit', 'proofread', 'summarize', 'rewrite']
        if any(keyword in query_lower for keyword in creative_keywords):
            topics.append("creative")

        # Analysis/Research indicators
        analysis_keywords = ['analyze', 'compare', 'evaluate', 'assess', 'review',
                             'research', 'study', 'investigate', 'examine', 'pros and cons',
                             'advantages', 'disadvantages', 'difference', 'similarity']
        if any(keyword in query_lower for keyword in analysis_keywords):
            topics.append("analysis")

        # Finance/Business indicators
        finance_keywords = ['money', 'budget', 'invest', 'stock', 'salary', 'price',
                            'cost', 'finance', 'bank', 'loan', 'tax', 'income',
                            'expense', 'profit', 'revenue', 'payment', 'credit',
                            'mortgage', 'insurance', 'savings', 'retirement']
        if any(keyword in query_lower for keyword in finance_keywords):
            topics.append("finance")

        # Travel indicators
        travel_keywords = ['travel', 'trip', 'flight', 'hotel', 'vacation', 'holiday',
                           'visit', 'tourism', 'destination', 'booking', 'passport',
                           'visa', 'airport', 'luggage', 'itinerary']
        if any(keyword in query_lower for keyword in travel_keywords):
            topics.append("travel")

        # Food/Cooking indicators
        food_keywords = ['recipe', 'cook', 'food', 'eat', 'restaurant', 'meal',
                         'ingredient', 'dish', 'cuisine', 'bake', 'dinner',
                         'breakfast', 'lunch', 'snack', 'drink', 'coffee', 'tea']
        if any(keyword in query_lower for keyword in food_keywords):
            topics.append("food")

        # Weather indicators
        weather_keywords = ['weather', 'temperature', 'rain', 'sunny', 'forecast',
                            'climate', 'snow', 'wind', 'humid', 'storm', 'cold', 'hot']
        if any(keyword in query_lower for keyword in weather_keywords):
            topics.append("weather")

        # Entertainment indicators
        entertainment_keywords = ['movie', 'film', 'music', 'song', 'game', 'play',
                                  'watch', 'show', 'series', 'netflix', 'youtube',
                                  'book', 'read', 'podcast', 'concert', 'theater']
        if any(keyword in query_lower for keyword in entertainment_keywords):
            topics.append("entertainment")

        # Education/Learning indicators
        education_keywords = ['learn', 'study', 'course', 'school', 'university',
                              'teach', 'education', 'exam', 'test', 'degree',
                              'certificate', 'tutorial', 'lesson', 'homework']
        if any(keyword in query_lower for keyword in education_keywords):
            topics.append("education")

        # Sports/Fitness indicators
        sports_keywords = ['sport', 'football', 'soccer', 'basketball', 'tennis',
                           'gym', 'fitness', 'workout', 'run', 'swim', 'yoga',
                           'team', 'match', 'score', 'player', 'championship']
        if any(keyword in query_lower for keyword in sports_keywords):
            topics.append("sports")

        # Shopping/Products indicators
        shopping_keywords = ['buy', 'purchase', 'product', 'shop', 'order',
                             'amazon', 'delivery', 'shipping', 'return', 'refund',
                             'discount', 'sale', 'brand', 'quality', 'recommend']
        if any(keyword in query_lower for keyword in shopping_keywords):
            topics.append("shopping")

        # Legal indicators
        legal_keywords = ['law', 'legal', 'lawyer', 'court', 'contract', 'rights',
                          'sue', 'lawsuit', 'attorney', 'judge', 'verdict', 'settlement']
        if any(keyword in query_lower for keyword in legal_keywords):
            topics.append("legal")

        # Science indicators
        science_keywords = ['science', 'physics', 'chemistry', 'biology', 'experiment',
                            'research', 'hypothesis', 'theory', 'formula', 'equation',
                            'atom', 'molecule', 'cell', 'dna', 'evolution']
        if any(keyword in query_lower for keyword in science_keywords):
            topics.append("science")

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

    def _calculate_confidence(self, query: str, entities: List[str], topics: List[str]) -> float:
        """Calculate confidence score (0-1) based on query clarity"""
        confidence = 1.0
        words = query.split()
        word_count = len(words)

        # Penalize very short queries (vague) - scaled by length
        if word_count == 1:
            confidence -= 0.5  # Single word = very low confidence
        elif word_count == 2:
            confidence -= 0.35  # Two words = low confidence
        elif word_count <= 3:
            confidence -= 0.2  # Three words = slight penalty

        # Penalize if no meaningful entities found (unclear)
        # Filter out common words that aren't real entities
        meaningful_entities = [e for e in entities if e.lower() not in
                               ['help', 'ok', 'yes', 'no', 'hmm', 'hey', 'hi', 'hello']]
        if len(meaningful_entities) == 0:
            confidence -= 0.2

        # Penalize if only "general" topic (not specific)
        if topics == ["general"]:
            confidence -= 0.2

        # Penalize very vague words
        vague_words = ['something', 'anything', 'stuff', 'thing', 'whatever']
        if any(word in query.lower() for word in vague_words):
            confidence -= 0.3

        # Penalize generic "tell me about" patterns (less specific)
        generic_patterns = ['tell me about', 'what about', 'how about']
        if any(pattern in query.lower() for pattern in generic_patterns):
            confidence -= 0.15

        # Ensure confidence stays in valid range [0.3, 1.0]
        confidence = max(0.3, min(1.0, confidence))

        return confidence