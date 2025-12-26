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