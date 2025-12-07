# ТЕХНИЧЕСКОЕ ЗАДАНИЕ
## Intelligent Orchestrator with Memory-Aware Reasoning

**Version:** 1.0  
**Date:** December 6, 2025  
**Author:** Denis (QA Engineer)  
**Project:** AI Agent System v2.0

---

## 1. EXECUTIVE SUMMARY

### 1.1 Цель
Разработать интеллектуальный Orchestrator, который принимает решения о необходимости дополнительного рассуждения на основе анализа запроса и доступной памяти.

### 1.2 Проблема
**Текущая система:**
- ❌ Все запросы обрабатываются одинаково
- ❌ Нет оценки сложности запроса
- ❌ Нет решения "нужно ли глубокое рассуждение"
- ❌ Память используется пассивно (просто добавляется в контекст)
- ❌ Нет планирования шагов

**Пример проблемы:**
```
User: "What's my name?"
Current: Полный запрос к AI → 3 секунды
Better:  Проверка памяти → мгновенный ответ

User: "Compare my investment strategy with current market trends"
Current: Простой ответ → недостаточно
Better:  Multi-step reasoning → качественный анализ
```

### 1.3 Решение
**Intelligent Orchestrator** с 5-этапным процессом принятия решений.

---

## 2. ВЫСОКОУРОВНЕВАЯ ЛОГИКА

### 2.1 Workflow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Query Analysis                                    │
│  - Parse intent                                             │
│  - Detect complexity level (simple/medium/complex)          │
│  - Extract entities & topics                                │
│  - Classify query type (factual/reasoning/creative)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: Memory Check                                      │
│  - Search relevant facts in memory                          │
│  - Calculate confidence score (0-1)                         │
│  - Identify information gaps                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: Decision Making                                   │
│                                                              │
│  IF confidence >= 0.9 AND query is simple:                  │
│     → Direct Answer (no reasoning)                          │
│                                                              │
│  ELIF confidence >= 0.7 AND query is medium:                │
│     → Enhanced Answer (light reasoning)                     │
│                                                              │
│  ELSE:                                                       │
│     → Deep Reasoning (multi-step)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┬─────────────┐
         ▼                           ▼             ▼
    Direct Answer            Enhanced Answer   Deep Reasoning
    (Stage 4a)               (Stage 4b)        (Stage 4c)
         │                           │             │
         └─────────────┬─────────────┴─────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: Response Formation                                │
│  - Format final answer                                      │
│  - Add sources & confidence                                 │
│  - Extract & save new facts                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                   RESPONSE
```

---

## 3. ДЕТАЛЬНАЯ СПЕЦИФИКАЦИЯ

### 3.1 STAGE 1: Query Analysis

**Компонент:** `QueryAnalyzer` (уже есть, нужно расширить)

**Входные данные:**
```python
{
    "query": str,
    "session_id": str,
    "user_context": dict  # preferences, history, etc.
}
```

**Выходные данные:**
```python
{
    "intent": str,  # "question", "command", "statement"
    "complexity": str,  # "simple", "medium", "complex"
    "query_type": str,  # "factual", "reasoning", "creative", "analytical"
    "entities": List[str],  # ["Denis", "Python", "QA"]
    "topics": List[str],  # ["programming", "testing"]
    "requires_memory": bool,
    "requires_reasoning": bool,
    "confidence": float  # 0-1
}
```

**Логика классификации:**
```python
class ComplexityClassifier:
    """
    Определяет сложность запроса
    """
    
    SIMPLE_PATTERNS = [
        r"^what is my (name|age|location)",  # Factual recall
        r"^(hi|hello|hey)",  # Greetings
        r"^(yes|no|ok|thanks)",  # Confirmations
    ]
    
    COMPLEX_PATTERNS = [
        r"compare .* with .*",  # Comparisons
        r"analyze|evaluate|assess",  # Analysis
        r"why .* and .*",  # Multi-part reasoning
        r"if .* then .*",  # Conditional logic
    ]
    
    def classify(self, query: str) -> str:
        query_lower = query.lower()
        
        # Simple
        if any(re.match(p, query_lower) for p in self.SIMPLE_PATTERNS):
            return "simple"
        
        # Complex
        if any(re.search(p, query_lower) for p in self.COMPLEX_PATTERNS):
            return "complex"
        
        # Medium (default)
        return "medium"
```

**Примеры:**
```python
"What is my name?" → 
    complexity="simple", requires_memory=True, requires_reasoning=False

"Explain quantum computing" → 
    complexity="medium", requires_memory=False, requires_reasoning=True

"Compare my investment strategy with market trends and suggest improvements" → 
    complexity="complex", requires_memory=True, requires_reasoning=True
```

---

### 3.2 STAGE 2: Memory Check

**Компонент:** `MemoryEvaluator` (новый)

**Функция:**
```python
async def evaluate_memory_coverage(
    query_analysis: QueryAnalysis,
    session_id: str
) -> MemoryEvaluation:
    """
    Оценивает насколько память может ответить на запрос
    """
    
    # 1. Search relevant facts
    relevant_facts = await memory_service.search_facts(
        query=query_analysis.query,
        session_id=session_id,
        threshold=0.7
    )
    
    # 2. Calculate coverage score
    coverage_score = calculate_coverage(
        query_entities=query_analysis.entities,
        found_facts=relevant_facts
    )
    
    # 3. Identify gaps
    information_gaps = identify_gaps(
        required_entities=query_analysis.entities,
        available_facts=relevant_facts
    )
    
    return MemoryEvaluation(
        relevant_facts=relevant_facts,
        coverage_score=coverage_score,  # 0-1
        information_gaps=information_gaps,
        can_answer_directly=coverage_score >= 0.9
    )
```

**Выходные данные:**
```python
{
    "relevant_facts": List[Fact],
    "coverage_score": float,  # 0-1 (насколько память покрывает запрос)
    "information_gaps": List[str],  # Что отсутствует
    "can_answer_directly": bool
}
```

**Примеры:**
```python
Query: "What is my name?"
Memory: [Fact("User's name is Denis", confidence=0.95)]
Result:
    coverage_score=1.0
    information_gaps=[]
    can_answer_directly=True

Query: "What's my investment strategy vs market trends?"
Memory: [Fact("User works in QA", confidence=0.9)]
Result:
    coverage_score=0.2
    information_gaps=["investment strategy", "market trends"]
    can_answer_directly=False
```

---

### 3.3 STAGE 3: Decision Making

**Компонент:** `ReasoningDecisionEngine` (новый)

**Decision Tree:**
```python
class ReasoningDecisionEngine:
    """
    Принимает решение о стратегии ответа
    """
    
    def decide_strategy(
        self,
        query_analysis: QueryAnalysis,
        memory_eval: MemoryEvaluation
    ) -> ResponseStrategy:
        
        # Rule 1: Direct Answer
        if (
            query_analysis.complexity == "simple" and
            memory_eval.can_answer_directly and
            not query_analysis.requires_reasoning
        ):
            return ResponseStrategy(
                type="direct",
                reasoning_depth=0,
                use_memory=True,
                use_ai=False  # Не нужен AI, просто facts
            )
        
        # Rule 2: Enhanced Answer (Light Reasoning)
        if (
            query_analysis.complexity == "medium" and
            memory_eval.coverage_score >= 0.7 and
            query_analysis.requires_reasoning
        ):
            return ResponseStrategy(
                type="enhanced",
                reasoning_depth=1,  # Single-step reasoning
                use_memory=True,
                use_ai=True,
                agent_preference="fast"  # Mistral, DeepSeek
            )
        
        # Rule 3: Deep Reasoning (Multi-step)
        if (
            query_analysis.complexity == "complex" or
            memory_eval.coverage_score < 0.7 or
            len(memory_eval.information_gaps) > 0
        ):
            return ResponseStrategy(
                type="deep_reasoning",
                reasoning_depth=3,  # Multi-step
                use_memory=True,
                use_ai=True,
                agent_preference="premium",  # Mixtral, GPT-OSS
                tools=["web_search"] if memory_eval.information_gaps else []
            )
        
        # Default: Enhanced
        return ResponseStrategy(type="enhanced", reasoning_depth=1)
```

**ResponseStrategy:**
```python
{
    "type": str,  # "direct", "enhanced", "deep_reasoning"
    "reasoning_depth": int,  # 0, 1, 2, 3+
    "use_memory": bool,
    "use_ai": bool,
    "agent_preference": str,  # "fast", "balanced", "premium"
    "tools": List[str],  # ["web_search", "document_search"]
    "estimated_time": float  # seconds
}
```

---

### 3.4 STAGE 4: Response Generation

#### 3.4.1 Direct Answer (No AI)
```python
async def generate_direct_answer(
    query: str,
    relevant_facts: List[Fact]
) -> DirectResponse:
    """
    Формирует ответ без AI, только из фактов
    """
    
    # Template-based response
    if query.lower().startswith("what is my name"):
        name_fact = find_fact_by_type(relevant_facts, "name")
        return f"Your name is {name_fact.text}."
    
    if query.lower().startswith("where do i live"):
        location_fact = find_fact_by_type(relevant_facts, "location")
        return f"You live in {location_fact.text}."
    
    # Fallback to facts list
    return format_facts_as_answer(relevant_facts)
```

**Преимущества:**
- ⚡ Мгновенный ответ (<100ms)
- 💰 Нет cost AI запроса
- ✅ 100% точность (из памяти)

#### 3.4.2 Enhanced Answer (Light Reasoning)
```python
async def generate_enhanced_answer(
    query: str,
    relevant_facts: List[Fact],
    strategy: ResponseStrategy
) -> EnhancedResponse:
    """
    AI делает single-step reasoning с фактами
    """
    
    # Build prompt
    prompt = f"""
Based on these facts about the user:
{format_facts(relevant_facts)}

Answer this question with brief reasoning:
{query}

Provide:
1. Direct answer
2. Brief explanation (1-2 sentences)
"""
    
    # Use fast agent
    agent = select_agent(strategy.agent_preference)  # Mistral or DeepSeek
    response = await agent.generate(prompt)
    
    return EnhancedResponse(
        answer=response,
        reasoning_steps=["Single-step inference from facts"],
        sources=["memory"],
        confidence=0.85
    )
```

#### 3.4.3 Deep Reasoning (Multi-step)
```python
async def generate_deep_reasoning_answer(
    query: str,
    query_analysis: QueryAnalysis,
    memory_eval: MemoryEvaluation,
    strategy: ResponseStrategy
) -> DeepReasoningResponse:
    """
    Multi-step reasoning с планированием
    """
    
    # Step 1: Planning
    plan = await create_reasoning_plan(query, memory_eval.information_gaps)
    # Plan: ["Recall user facts", "Search market trends", "Compare", "Synthesize"]
    
    steps_results = []
    
    # Step 2: Execute plan
    for step in plan.steps:
        if step.type == "recall":
            result = await memory_service.search_facts(step.query)
        
        elif step.type == "search":
            result = await web_search_tool.search(step.query)
        
        elif step.type == "reason":
            result = await premium_agent.generate(step.prompt, context=steps_results)
        
        steps_results.append(result)
    
    # Step 3: Synthesize
    final_prompt = f"""
Based on these reasoning steps:
{format_steps(steps_results)}

Provide a comprehensive answer to: {query}
"""
    
    agent = select_agent("premium")  # Mixtral or GPT-OSS
    final_answer = await agent.generate(final_prompt)
    
    return DeepReasoningResponse(
        answer=final_answer,
        reasoning_steps=[step.description for step in plan.steps],
        intermediate_results=steps_results,
        sources=["memory", "web_search"],
        confidence=0.92,
        reasoning_depth=len(plan.steps)
    )
```

---

### 3.5 STAGE 5: Response Formation

**Компонент:** `ResponseFormatter` (новый)
```python
class ResponseFormatter:
    """
    Форматирует финальный ответ для пользователя
    """
    
    def format_response(
        self,
        strategy_type: str,
        response: Union[DirectResponse, EnhancedResponse, DeepReasoningResponse]
    ) -> FormattedResponse:
        
        formatted = {
            "text": response.answer,
            "metadata": {
                "strategy": strategy_type,
                "confidence": response.confidence,
                "sources": response.sources,
                "reasoning_depth": getattr(response, "reasoning_depth", 0),
                "response_time_ms": response.elapsed_time
            }
        }
        
        # Add reasoning trace for debugging
        if hasattr(response, "reasoning_steps"):
            formatted["debug"] = {
                "reasoning_steps": response.reasoning_steps,
                "intermediate_results": getattr(response, "intermediate_results", [])
            }
        
        return formatted
```

---

## 4. АРХИТЕКТУРА КОМПОНЕНТОВ

### 4.1 Новые компоненты
```
app/services/orchestrator/
├── __init__.py
├── query_analyzer.py          # Query analysis (расширенный)
├── memory_evaluator.py        # Memory coverage evaluation
├── decision_engine.py         # Decision tree logic
├── reasoning_engine.py        # Multi-step reasoning
├── response_formatter.py      # Response formatting
└── orchestrator.py           # Main orchestrator class
```

### 4.2 Main Orchestrator Class
```python
class IntelligentOrchestrator:
    """
    Главный оркестратор с интеллектуальным принятием решений
    """
    
    def __init__(
        self,
        memory_service: MemoryService,
        agent_registry: AgentRegistry,
        query_analyzer: QueryAnalyzer,
        memory_evaluator: MemoryEvaluator,
        decision_engine: ReasoningDecisionEngine,
        reasoning_engine: ReasoningEngine,
        response_formatter: ResponseFormatter
    ):
        self.memory_service = memory_service
        self.agent_registry = agent_registry
        self.query_analyzer = query_analyzer
        self.memory_evaluator = memory_evaluator
        self.decision_engine = decision_engine
        self.reasoning_engine = reasoning_engine
        self.response_formatter = response_formatter
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        user_context: Optional[dict] = None
    ) -> OrchestratedResponse:
        """
        Главный метод обработки запроса
        """
        
        # STAGE 1: Analyze query
        query_analysis = await self.query_analyzer.analyze(
            query=query,
            session_id=session_id,
            user_context=user_context
        )
        
        # STAGE 2: Check memory
        memory_eval = await self.memory_evaluator.evaluate_memory_coverage(
            query_analysis=query_analysis,
            session_id=session_id
        )
        
        # STAGE 3: Decide strategy
        strategy = self.decision_engine.decide_strategy(
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )
        
        # STAGE 4: Generate response
        if strategy.type == "direct":
            response = await self._generate_direct_answer(
                query, memory_eval.relevant_facts
            )
        elif strategy.type == "enhanced":
            response = await self._generate_enhanced_answer(
                query, memory_eval.relevant_facts, strategy
            )
        else:  # deep_reasoning
            response = await self._generate_deep_reasoning_answer(
                query, query_analysis, memory_eval, strategy
            )
        
        # STAGE 5: Format response
        formatted_response = self.response_formatter.format_response(
            strategy_type=strategy.type,
            response=response
        )
        
        # Save new facts
        await self._extract_and_save_facts(
            session_id=session_id,
            query=query,
            response=formatted_response.text
        )
        
        return OrchestratedResponse(
            text=formatted_response.text,
            metadata=formatted_response.metadata,
            debug=formatted_response.debug
        )
```

---

## 5. ПРИМЕРЫ РАБОТЫ

### Пример 1: Simple Query (Direct Answer)

**Input:**
```python
query = "What is my name?"
session_id = "abc123"
```

**STAGE 1: Query Analysis**
```python
{
    "complexity": "simple",
    "query_type": "factual",
    "entities": ["name"],
    "requires_memory": True,
    "requires_reasoning": False
}
```

**STAGE 2: Memory Check**
```python
{
    "relevant_facts": [
        Fact("User's name is Denis", confidence=0.95)
    ],
    "coverage_score": 1.0,
    "can_answer_directly": True
}
```

**STAGE 3: Decision**
```python
strategy = "direct"  # No AI needed!
```

**STAGE 4: Response**
```python
response = "Your name is Denis."
time = 50ms
cost = $0
```

---

### Пример 2: Medium Query (Enhanced Answer)

**Input:**
```python
query = "What programming languages do I know and which should I learn next?"
session_id = "abc123"
```

**STAGE 1: Query Analysis**
```python
{
    "complexity": "medium",
    "query_type": "analytical",
    "entities": ["programming languages"],
    "requires_memory": True,
    "requires_reasoning": True
}
```

**STAGE 2: Memory Check**
```python
{
    "relevant_facts": [
        Fact("Denis loves Python programming", confidence=0.9),
        Fact("Denis works as QA Engineer", confidence=0.95)
    ],
    "coverage_score": 0.7,
    "can_answer_directly": False  # Не хватает инфо про "learn next"
}
```

**STAGE 3: Decision**
```python
strategy = "enhanced"  # Light reasoning needed
agent = "mistral"
```

**STAGE 4: Response**
```python
prompt = """
Based on these facts:
- Denis loves Python programming
- Denis works as QA Engineer

Answer: What programming languages should Denis learn next?
Provide brief reasoning (2 sentences).
"""

response = """
Based on your Python expertise and QA role, I recommend learning JavaScript 
for web automation testing (Playwright/Cypress) and Go for performance 
testing tools. Both complement Python well and are highly valued in QA 
engineering.
"""

time = 2500ms
cost = $0.0003
```

---

### Пример 3: Complex Query (Deep Reasoning)

**Input:**
```python
query = """
Compare my current investment strategy with recent market trends, 
considering my risk tolerance and financial goals.
"""
session_id = "abc123"
```

**STAGE 1: Query Analysis**
```python
{
    "complexity": "complex",
    "query_type": "analytical",
    "entities": ["investment strategy", "market trends", "risk tolerance", "financial goals"],
    "requires_memory": True,
    "requires_reasoning": True
}
```

**STAGE 2: Memory Check**
```python
{
    "relevant_facts": [
        Fact("Denis works as QA Engineer in medical software", confidence=0.95)
    ],
    "coverage_score": 0.2,
    "information_gaps": [
        "investment strategy",
        "market trends",
        "risk tolerance",
        "financial goals"
    ],
    "can_answer_directly": False
}
```

**STAGE 3: Decision**
```python
strategy = "deep_reasoning"
reasoning_depth = 4
agent = "mixtral"  # Premium model
tools = ["web_search"]
```

**STAGE 4: Multi-Step Reasoning**
```python
# Step 1: Check memory for user financial info
memory_results = await memory.search("investment financial goals")
# Result: No specific investment data found

# Step 2: Search current market trends
market_trends = await web_search("current market trends December 2025")
# Result: [Articles about tech stocks, interest rates, etc.]

# Step 3: Request user info (if not in memory)
needs_clarification = True
clarification_questions = [
    "What's your current investment strategy?",
    "What's your risk tolerance (low/medium/high)?",
    "What are your financial goals?"
]

# Step 4: Synthesize (if user provides info) or ask for clarification
response = f"""
I'd like to help you compare your investment strategy with current market 
trends, but I need some information first:

1. What's your current investment strategy? (e.g., stocks, bonds, real estate)
2. What's your risk tolerance? (conservative, moderate, aggressive)
3. What are your financial goals? (retirement, home purchase, wealth building)

Once you provide this information, I can analyze how well your strategy 
aligns with current market conditions.
"""

time = 8500ms
cost = $0.003
```

---

## 6. МЕТРИКИ И ОПТИМИЗАЦИЯ

### 6.1 Key Performance Indicators
```python
# Response time by strategy
PERFORMANCE_TARGETS = {
    "direct": 100,      # ms
    "enhanced": 3000,   # ms
    "deep_reasoning": 15000  # ms
}

# Cost per query
COST_TARGETS = {
    "direct": 0,        # $
    "enhanced": 0.0003, # $
    "deep_reasoning": 0.005  # $
}

# Accuracy
ACCURACY_TARGETS = {
    "direct": 0.99,     # From memory
    "enhanced": 0.90,   # AI + memory
    "deep_reasoning": 0.95  # Multi-step
}
```

### 6.2 Monitoring
```python
class OrchestratorMetrics:
    """
    Отслеживание метрик оркестратора
    """
    
    def track_query(
        self,
        query_analysis: QueryAnalysis,
        strategy: ResponseStrategy,
        response: OrchestratedResponse,
        elapsed_time: float
    ):
        metrics = {
            "timestamp": datetime.utcnow(),
            "complexity": query_analysis.complexity,
            "strategy": strategy.type,
            "reasoning_depth": strategy.reasoning_depth,
            "elapsed_time_ms": elapsed_time * 1000,
            "cost_usd": calculate_cost(response),
            "memory_coverage": response.metadata.get("memory_coverage", 0),
            "user_satisfaction": None  # Filled by user feedback
        }
        
        # Log to database
        await self.metrics_db.insert(metrics)
        
        # Alert if performance issue
        if elapsed_time > PERFORMANCE_TARGETS[strategy.type] / 1000:
            logger.warning(f"Slow response: {elapsed_time}s for {strategy.type}")
```

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests
```python
# test_query_analyzer.py
def test_simple_query_classification():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("What is my name?")
    assert result.complexity == "simple"
    assert result.requires_memory == True
    assert result.requires_reasoning == False

def test_complex_query_classification():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze(
        "Compare my investment strategy with market trends"
    )
    assert result.complexity == "complex"
    assert result.requires_memory == True
    assert result.requires_reasoning == True

# test_memory_evaluator.py
@pytest.mark.asyncio
async def test_high_coverage_score():
    evaluator = MemoryEvaluator(memory_service)
    
    # Mock memory with relevant fact
    mock_facts = [Fact("User's name is Denis", confidence=0.95)]
    
    evaluation = await evaluator.evaluate_coverage(
        query="What is my name?",
        session_id="test"
    )
    
    assert evaluation.coverage_score >= 0.9
    assert evaluation.can_answer_directly == True

# test_decision_engine.py
def test_direct_answer_decision():
    engine = ReasoningDecisionEngine()
    
    query_analysis = QueryAnalysis(complexity="simple")
    memory_eval = MemoryEvaluation(coverage_score=1.0)
    
    strategy = engine.decide_strategy(query_analysis, memory_eval)
    
    assert strategy.type == "direct"
    assert strategy.use_ai == False
```

### 7.2 Integration Tests
```python
@pytest.mark.asyncio
async def test_end_to_end_simple_query():
    orchestrator = IntelligentOrchestrator(...)
    
    # Add fact to memory
    await memory_service.add_fact(
        session_id="test",
        text="User's name is Denis",
        importance=0.95
    )
    
    # Process query
    response = await orchestrator.process_query(
        query="What is my name?",
        session_id="test"
    )
    
    # Assertions
    assert "Denis" in response.text
    assert response.metadata["strategy"] == "direct"
    assert response.metadata["response_time_ms"] < 100

@pytest.mark.asyncio
async def test_end_to_end_complex_query():
    orchestrator = IntelligentOrchestrator(...)
    
    response = await orchestrator.process_query(
        query="Compare quantum computing with classical computing",
        session_id="test"
    )
    
    assert response.metadata["strategy"] == "deep_reasoning"
    assert response.metadata["reasoning_depth"] > 1
    assert len(response.debug["reasoning_steps"]) > 2
```

---

## 8. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 5) - 8 hours
```
✅ Task 1: QueryAnalyzer расширение (2h)
   - Добавить complexity classification
   - Добавить entity extraction
   - Тесты

✅ Task 2: MemoryEvaluator (2h)
   - Implement coverage calculation
   - Implement gap detection
   - Тесты

✅ Task 3: DecisionEngine (2h)
   - Implement decision tree
   - Strategy selection logic
   - Тесты

✅ Task 4: Basic Orchestrator (2h)
   - Integrate components
   - Implement direct answer path
   - Тесты
```

### Phase 2: Enhanced Reasoning (Week 6) - 8 hours
```
✅ Task 5: Enhanced Answer (3h)
   - Implement light reasoning
   - Agent selection logic
   - Тесты

✅ Task 6: Response Formatter (1h)
   - Format output
   - Add metadata
   - Тесты

✅ Task 7: Metrics & Monitoring (2h)
   - Performance tracking
   - Cost tracking
   - Alerting

✅ Task 8: Integration (2h)
   - Replace EnhancedChatService
   - Update routes
   - E2E tests
```

### Phase 3: Deep Reasoning (Week 7) - 12 hours
```
✅ Task 9: Reasoning Planner (4h)
   - Multi-step planning
   - Step execution
   - Tесты

✅ Task 10: Tool Integration (3h)
   - Web search integration
   - Document search integration
   - Тесты

✅ Task 11: Synthesis Engine (3h)
   - Multi-source synthesis
   - Confidence calculation
   - Тесты

✅ Task 12: Polish & Optimize (2h)
   - Performance optimization
   - Edge cases
   - Documentation
```

---

## 9. API SPECIFICATION

### 9.1 Orchestrator Endpoint
```python
@router.post("/api/v1/orchestrate")
async def orchestrate_query(
    request: OrchestrateRequest,
    current_user: User = Depends(get_current_user)
) -> OrchestratedResponse:
    """
    Intelligent query orchestration with reasoning
    """
    
    response = await orchestrator.process_query(
        query=request.query,
        session_id=request.session_id,
        user_context={
            "user_id": current_user.id,
            "preferences": current_user.preferences
        }
    )
    
    return response

# Request model
class OrchestrateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: str
    include_debug: bool = False

# Response model
class OrchestratedResponse(BaseModel):
    text: str
    metadata: OrchestratorMetadata
    debug: Optional[DebugInfo] = None

class OrchestratorMetadata(BaseModel):
    strategy: str  # "direct", "enhanced", "deep_reasoning"
    confidence: float
    sources: List[str]
    reasoning_depth: int
    response_time_ms: float
    cost_usd: float

class DebugInfo(BaseModel):
    query_analysis: QueryAnalysis
    memory_evaluation: MemoryEvaluation
    reasoning_steps: List[str]
    intermediate_results: List[dict]
```

---

## 10. CONFIGURATION
```yaml
# config/orchestrator.yaml

orchestrator:
  # Decision thresholds
  direct_answer_threshold: 0.9
  enhanced_answer_threshold: 0.7
  
  # Performance limits
  max_reasoning_depth: 5
  max_response_time_seconds: 30
  max_cost_per_query: 0.01
  
  # Agent preferences by strategy
  agent_mapping:
    direct: null  # No agent needed
    enhanced:
      - mistral
      - deepseek
      - llama3.1
    deep_reasoning:
      - mixtral
      - gpt-oss
      - groq
  
  # Memory settings
  memory:
    min_coverage_for_direct: 0.9
    min_confidence_for_facts: 0.7
    max_facts_to_retrieve: 20
  
  # Monitoring
  metrics:
    enabled: true
    log_all_queries: true
    alert_on_slow_response: true
```

---

## 11. SUMMARY

### Что получаем:

**✅ Интеллектуальное принятие решений:**
- Анализ сложности запроса
- Оценка покрытия памятью
- Выбор оптимальной стратегии

**✅ Три стратегии ответа:**
- Direct: мгновенно из памяти (100ms, $0)
- Enhanced: лёгкое рассуждение (3s, $0.0003)
- Deep: глубокое рассуждение (15s, $0.005)

**✅ Оптимизация:**
- Меньше cost (не все запросы идут в AI)
- Быстрее ответы (прямые из памяти)
- Выше качество (deep reasoning когда нужно)

**✅ Прозрачность:**
- Метрики по каждому запросу
- Debug информация
- Reasoning trace

---

## 12. NEXT STEPS

1. **Review этого ТЗ** (Denis + команда)
2. **Приоритизация:** Какие фазы делать сначала?
3. **Estimation:** Детальная оценка времени
4. **Start:** Phase 1 (Week 5?)

---

**Document Version:** 1.0  
**Last Updated:** December 6, 2025  
**Status:** DRAFT for Review  
**Reviewers:** Denis (QA Engineer)