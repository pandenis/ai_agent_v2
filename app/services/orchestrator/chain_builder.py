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

    def get_parallel_groups(self, chain: ExecutionChain) -> List[List[int]]:
        """
        Identify groups of steps that can run in parallel.

        Args:
            chain: Execution chain to analyze

        Returns:
            List of groups, each group contains step indices that can run in parallel
        """
        if not chain.steps:
            return []

        groups = []
        executed = set()

        while len(executed) < len(chain.steps):
            # Find steps whose dependencies are all executed
            ready = []
            for i, step in enumerate(chain.steps):
                if i not in executed:
                    if all(dep in executed for dep in step.depends_on):
                        ready.append(i)

            if ready:
                groups.append(ready)
                executed.update(ready)
            else:
                break  # Prevent infinite loop if dependencies are broken

        return groups

    def get_chain_stats(self, chain: ExecutionChain) -> dict:
        """
        Get statistics about execution chain.

        Args:
            chain: Execution chain to analyze

        Returns:
            Dictionary with chain statistics
        """
        parallel_groups = self.get_parallel_groups(chain)
        max_parallel = max((len(g) for g in parallel_groups), default=0)

        # Estimate time saved by parallel execution
        # Sequential: N steps, Parallel: number of groups
        sequential_steps = len(chain.steps)
        parallel_steps = len(parallel_groups)
        time_saved_percent = 0
        if sequential_steps > 0:
            time_saved_percent = round((1 - parallel_steps / sequential_steps) * 100, 1)

        return {
            "total_steps": len(chain.steps),
            "parallel_groups": len(parallel_groups),
            "max_parallel": max_parallel,
            "estimated_time_saved": f"{time_saved_percent}%",
        }