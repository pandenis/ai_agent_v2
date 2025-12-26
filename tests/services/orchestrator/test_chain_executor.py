"""
ChainExecutor - Executes multi-step chains with parallel support.

Features:
- Sequential execution
- Parallel execution (where possible)
- Error handling per step
- Result aggregation

Usage:
    >>> executor = ChainExecutor()
    >>> result = await executor.execute(chain)
    >>> print(result.success)
"""

import pytest
from app.services.orchestrator.chain_executor import StepResult


class TestChainExecutor:
    """Tests for ChainExecutor component."""

    def test_step_result_creation(self):
        """Test: StepResult holds step execution result."""
        # Arrange & Act
        result = StepResult(
            step_index=0,
            step_type="memory",
            success=True,
            output="User context retrieved",
            error=None,
            elapsed_ms=150.5
        )

        # Assert
        assert result.step_index == 0
        assert result.step_type == "memory"
        assert result.success is True
        assert result.output == "User context retrieved"
        assert result.error is None
        assert result.elapsed_ms == 150.5

    def test_chain_result_creation(self):
        """Test: ChainResult holds complete chain execution result."""
        # Arrange
        step_results = [
            StepResult(step_index=0, step_type="memory", success=True, output="data", error=None, elapsed_ms=100),
            StepResult(step_index=1, step_type="analysis", success=True, output="result", error=None, elapsed_ms=200),
        ]

        # Act
        from app.services.orchestrator.chain_executor import ChainResult
        result = ChainResult(
            success=True,
            steps=step_results,
            final_output="Final answer",
            total_elapsed_ms=300,
            error=None
        )

        # Assert
        assert result.success is True
        assert len(result.steps) == 2
        assert result.final_output == "Final answer"
        assert result.total_elapsed_ms == 300

    @pytest.mark.asyncio
    async def test_execute_simple_chain(self):
        """Test: Execute simple single-step chain."""
        # Arrange
        from app.services.orchestrator.chain_builder import ChainStep, ExecutionChain
        from app.services.orchestrator.chain_executor import ChainExecutor

        chain = ExecutionChain(
            steps=[
                ChainStep(step_type="direct", agent="memory", prompt="What is my name?", depends_on=[])
            ],
            query="What is my name?"
        )

        executor = ChainExecutor()

        # Act
        result = await executor.execute(chain)

        # Assert
        assert result.success is True
        assert len(result.steps) == 1
        assert result.steps[0].step_type == "direct"
        assert result.total_elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_with_step_handler(self):
        """Test: Execute chain with custom step handler."""
        # Arrange
        from app.services.orchestrator.chain_builder import ChainStep, ExecutionChain
        from app.services.orchestrator.chain_executor import ChainExecutor

        chain = ExecutionChain(
            steps=[
                ChainStep(step_type="memory", agent="memory", prompt="Get context", depends_on=[]),
                ChainStep(step_type="analysis", agent="mistral", prompt="Analyze", depends_on=[0]),
            ],
            query="Test query"
        )

        # Custom handler returns specific output based on step type
        async def custom_handler(step, previous_results):
            if step.step_type == "memory":
                return "User likes Python"
            elif step.step_type == "analysis":
                return f"Analysis based on: {previous_results[0].output}"
            return "Unknown"

        executor = ChainExecutor(step_handler=custom_handler)

        # Act
        result = await executor.execute(chain)

        # Assert
        assert result.success is True
        assert result.steps[0].output == "User likes Python"
        assert "User likes Python" in result.steps[1].output

    @pytest.mark.asyncio
    async def test_execute_handles_step_failure(self):
        """Test: Chain handles step failure gracefully."""
        # Arrange
        from app.services.orchestrator.chain_builder import ChainStep, ExecutionChain
        from app.services.orchestrator.chain_executor import ChainExecutor

        chain = ExecutionChain(
            steps=[
                ChainStep(step_type="memory", agent="memory", prompt="Get context", depends_on=[]),
                ChainStep(step_type="web_search", agent="web", prompt="Search", depends_on=[]),
            ],
            query="Test query"
        )

        # Handler that fails on web_search
        async def failing_handler(step, previous_results):
            if step.step_type == "web_search":
                raise Exception("Network error")
            return "Success"

        executor = ChainExecutor(step_handler=failing_handler)

        # Act
        result = await executor.execute(chain)

        # Assert
        assert result.success is False
        assert result.steps[0].success is True
        assert result.steps[1].success is False
        assert "Network error" in result.steps[1].error

    @pytest.mark.asyncio
    async def test_execute_empty_chain(self):
        """Test: Execute empty chain returns success with no steps."""
        # Arrange
        from app.services.orchestrator.chain_builder import ExecutionChain
        from app.services.orchestrator.chain_executor import ChainExecutor

        chain = ExecutionChain(steps=[], query="Empty")
        executor = ChainExecutor()

        # Act
        result = await executor.execute(chain)

        # Assert
        assert result.success is True
        assert len(result.steps) == 0
        assert result.final_output is None

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test: Get execution statistics."""
        # Arrange
        from app.services.orchestrator.chain_builder import ChainStep, ExecutionChain
        from app.services.orchestrator.chain_executor import ChainExecutor

        chain = ExecutionChain(
            steps=[
                ChainStep(step_type="memory", agent="memory", prompt="Get", depends_on=[]),
                ChainStep(step_type="analysis", agent="ai", prompt="Analyze", depends_on=[0]),
            ],
            query="Test"
        )
        executor = ChainExecutor()

        # Act
        result = await executor.execute(chain)
        stats = executor.get_stats()

        # Assert
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["failed_executions"] == 0
        assert "avg_elapsed_ms" in stats