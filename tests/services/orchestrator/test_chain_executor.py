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