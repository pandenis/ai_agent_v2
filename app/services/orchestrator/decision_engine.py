"""
DecisionEngine - Decides optimal response strategy using rule-based logic.

This component makes intelligent decisions about how to respond to queries
based on query analysis and memory evaluation. It uses simple IF-THEN rules
(NO LLM needed) to select the best strategy and agent.

Decision Rules:
1. DIRECT (coverage ≥ 0.9 + simple):
   - Answer from memory only
   - No AI needed
   - Cost: $0, Time: ~100ms

2. ENHANCED (coverage ≥ 0.7 + simple/medium):
   - AI with memory context
   - Agent selected by topic
   - Cost: ~$0.0003, Time: ~3s

3. DEEP REASONING (everything else):
   - Multi-step AI reasoning
   - Powerful model (mixtral)
   - Cost: ~$0.005, Time: ~15s

Agent Selection:
- programming → deepseek
- medical → medical_ai
- creative → mistral
- analysis → mixtral
- default → llama3

Usage:
    >>> engine = DecisionEngine()
    >>> decision = engine.decide(query_analysis, memory_eval)
    >>> print(f"Strategy: {decision.strategy}")
    >>> print(f"Agent: {decision.agent}")
    >>> print(f"Cost: ${decision.estimated_cost}")
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Decision:
    """Decision result with complete metadata"""
    strategy: str  # "direct", "enhanced", "deep_reasoning"
    agent: Optional[str]  # AI agent to use (None for direct)
    use_memory: bool  # Whether to use memory
    estimated_time: float  # Seconds
    estimated_cost: float  # USD

    # Additional fields needed by orchestrator
    reasoning_depth: int = 0  # 0, 1, 2-4
    use_ai: bool = True  # Whether AI is needed
    agent_preference: str = "balanced"  # "fast", "balanced", "premium"
    tools: List[str] = field(default_factory=list)  # Tools to use (web_search, etc.)
    confidence: float = 0.9  # Confidence in decision (0-1)

    def __post_init__(self):
        """Set intelligent defaults after initialization"""
        # Set use_ai based on strategy
        if self.strategy == "direct":
            self.use_ai = False

        # Set reasoning_depth based on strategy
        if self.strategy == "direct":
            self.reasoning_depth = 0
        elif self.strategy == "enhanced":
            self.reasoning_depth = 1
        else:  # deep_reasoning
            self.reasoning_depth = 3

        # Set agent_preference based on strategy
        if self.strategy == "direct":
            self.agent_preference = "none"
        elif self.strategy == "enhanced":
            self.agent_preference = "balanced"
        else:
            self.agent_preference = "premium"


class DecisionEngine:
    """Makes decisions about response strategy"""

    # Agent selection by topic
    AGENT_MAP = {
        "programming": "deepseek",
        "medical": "medical_ai",
        "creative": "mistral",
        "analysis": "mixtral",
        "general": "llama3"
    }

    def decide(self, query_analysis, memory_eval) -> Decision:
        """Decide optimal strategy based on query and memory"""

        # RULE 1: Direct answer (high coverage + simple)
        if (query_analysis.complexity == "simple"
                and memory_eval.coverage_score >= 0.9):
            return Decision(
                strategy="direct",
                agent=None,
                use_memory=True,
                estimated_time=0.1,
                estimated_cost=0.0
            )

        # RULE 2: Enhanced answer (medium coverage + not complex)
        elif (query_analysis.complexity in ["simple", "medium"]
              and memory_eval.coverage_score >= 0.7):
            agent = self._select_agent(query_analysis.topics)
            return Decision(
                strategy="enhanced",
                agent=agent,
                use_memory=True,
                estimated_time=3.0,
                estimated_cost=0.0003
            )

        # RULE 3: Deep reasoning (everything else)
        else:
            return Decision(
                strategy="deep_reasoning",
                agent="mixtral",
                use_memory=True,
                estimated_time=15.0,
                estimated_cost=0.005
            )

    def _select_agent(self, topics: list) -> str:
        """Select best agent for topics"""
        # Use first topic to select agent
        if topics:
            first_topic = topics[0]
            return self.AGENT_MAP.get(first_topic, "llama3")
        return "llama3"


# Alias for compatibility with orchestrator
ResponseStrategy = Decision