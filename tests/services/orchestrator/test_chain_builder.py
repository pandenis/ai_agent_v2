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
from app.services.orchestrator.chain_builder import ChainStep, ExecutionChain, ChainBuilder

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

    def test_execution_chain_creation(self):
        """Test: ExecutionChain holds list of steps with metadata."""
        # Arrange
        steps = [
            ChainStep(step_type="memory", agent="gpt-oss", prompt="Get context"),
            ChainStep(step_type="analysis", agent="mistral", prompt="Analyze"),
        ]

        # Act
        from app.services.orchestrator.chain_builder import ExecutionChain
        chain = ExecutionChain(steps=steps, query="Test query")

        # Assert
        assert len(chain.steps) == 2
        assert chain.query == "Test query"
        assert chain.steps[0].step_type == "memory"
        assert chain.steps[1].step_type == "analysis"

    def test_build_simple_query_single_step(self):
        """Test: Simple query with high memory coverage creates single step."""
        # Arrange
        from app.services.orchestrator.chain_builder import ChainBuilder
        builder = ChainBuilder()

        # High coverage = simple direct answer
        memory_coverage = 0.95
        query = "What is my name?"

        # Act
        chain = builder.build(query=query, memory_coverage=memory_coverage)

        # Assert
        assert len(chain.steps) == 1
        assert chain.steps[0].step_type == "direct"
        assert chain.query == query

    def test_build_medium_coverage_creates_enhanced_chain(self):
        """Test: Medium coverage creates memory + AI chain."""
        # Arrange
        builder = ChainBuilder()
        memory_coverage = 0.75
        query = "Summarize my recent activities"

        # Act
        chain = builder.build(query=query, memory_coverage=memory_coverage)

        # Assert
        assert len(chain.steps) == 2
        assert chain.steps[0].step_type == "memory"
        assert chain.steps[1].step_type == "analysis"
        assert chain.steps[1].depends_on == [0]  # Depends on memory step

    def test_build_low_coverage_creates_deep_reasoning_chain(self):
        """Test: Low coverage creates full chain with web search."""
        # Arrange
        builder = ChainBuilder()
        memory_coverage = 0.3
        query = "Compare market trends with my investment strategy"

        # Act
        chain = builder.build(query=query, memory_coverage=memory_coverage)

        # Assert
        assert len(chain.steps) >= 3
        step_types = [s.step_type for s in chain.steps]
        assert "memory" in step_types
        assert "web_search" in step_types
        assert "synthesis" in step_types

    def test_get_parallel_groups(self):
        """Test: Identifies steps that can run in parallel."""
        # Arrange
        builder = ChainBuilder()
        chain = builder.build(query="Complex query", memory_coverage=0.3)

        # Act
        parallel_groups = builder.get_parallel_groups(chain)

        # Assert
        # memory and web_search have no dependencies - can run in parallel
        assert len(parallel_groups) >= 2
        assert len(parallel_groups[0]) == 2  # memory + web_search together
        assert parallel_groups[0] == [0, 1]  # step indices

    def test_get_parallel_groups_empty_chain(self):
        """Test: Empty chain returns empty groups."""
        # Arrange
        builder = ChainBuilder()
        chain = ExecutionChain(steps=[], query="Empty")

        # Act
        parallel_groups = builder.get_parallel_groups(chain)

        # Assert
        assert parallel_groups == []