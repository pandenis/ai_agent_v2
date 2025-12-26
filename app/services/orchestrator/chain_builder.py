"""
ChainBuilder - Plans multi-step execution chains for complex queries.

Features:
- ChainStep definition with agent and prompt
- ExecutionChain with ordered steps
- Dependency detection between steps
- Parallel execution detection

Usage:
    >>> builder = ChainBuilder()
    >>> chain = builder.build(query, memory_eval, available_agents)
    >>> print(chain.steps)
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ChainStep:
    """Single step in execution chain."""
    step_type: str
    agent: str
    prompt: str
    depends_on: List[int] = field(default_factory=list)

@dataclass
class ExecutionChain:
    """Complete execution chain with ordered steps."""
    steps: List[ChainStep]
    query: str

class ChainBuilder:
    """Builds multi-step execution chains for complex queries."""

    def build(self, query: str, memory_coverage: float) -> ExecutionChain:
        """
        Build execution chain based on query and memory coverage.

        Args:
            query: User query
            memory_coverage: Memory coverage score (0.0 - 1.0)

        Returns:
            ExecutionChain with planned steps
        """
        steps = []

        # High coverage = direct answer
        if memory_coverage >= 0.9:
            steps.append(ChainStep(
                step_type="direct",
                agent="memory",
                prompt=query,
                depends_on=[]
            ))
        # Medium coverage = memory + AI analysis
        elif memory_coverage >= 0.7:
            steps.append(ChainStep(
                step_type="memory",
                agent="memory",
                prompt="Retrieve relevant context",
                depends_on=[]
            ))
            steps.append(ChainStep(
                step_type="analysis",
                agent="mistral",
                prompt=query,
                depends_on=[0]
            ))
        # Low coverage = full chain with web search
        else:
            steps.append(ChainStep(
                step_type="memory",
                agent="memory",
                prompt="Retrieve available context",
                depends_on=[]
            ))
            steps.append(ChainStep(
                step_type="web_search",
                agent="web",
                prompt=f"Search for: {query}",
                depends_on=[]
            ))
            steps.append(ChainStep(
                step_type="analysis",
                agent="mixtral",
                prompt=query,
                depends_on=[0, 1]
            ))
            steps.append(ChainStep(
                step_type="synthesis",
                agent="mixtral",
                prompt="Synthesize final answer",
                depends_on=[2]
            ))

        return ExecutionChain(steps=steps, query=query)