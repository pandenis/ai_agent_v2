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

import pytest
from app.services.orchestrator.chain_builder import ChainStep


class TestChainBuilder:
    """Tests for ChainBuilder component."""

    def test_chain_step_creation(self):
        """Test: ChainStep dataclass holds step information."""
        # Arrange & Act
        step = ChainStep(
            step_type="memory",
            agent="gpt-oss",
            prompt="Retrieve user context",
            depends_on=[]
        )

        # Assert
        assert step.step_type == "memory"
        assert step.agent == "gpt-oss"
        assert step.prompt == "Retrieve user context"
        assert step.depends_on == []