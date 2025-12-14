"""
DecisionEngine - Decides optimal response strategy.

Rule-based decision logic (NO LLM) that selects:
- Strategy: direct/enhanced/deep_reasoning
- Agent: best AI agent for the topic
- Estimates: time and cost
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    """Decision result"""
    strategy: str  # "direct", "enhanced", "deep_reasoning"
    agent: Optional[str]  # AI agent to use (None for direct)
    use_memory: bool  # Whether to use memory
    estimated_time: float  # Seconds
    estimated_cost: float  # USD


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
