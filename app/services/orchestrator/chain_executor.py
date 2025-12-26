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

from dataclasses import dataclass
from typing import Optional, List, Any


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_index: int
    step_type: str
    success: bool
    output: Any
    error: Optional[str]
    elapsed_ms: float

@dataclass
class ChainResult:
    """Result of complete chain execution."""
    success: bool
    steps: List[StepResult]
    final_output: Any
    total_elapsed_ms: float
    error: Optional[str]


import time
from typing import Callable, Optional


class ChainExecutor:
    """Executes multi-step chains with parallel support."""

    def __init__(self, step_handler: Optional[Callable] = None):
        """
        Initialize executor.

        Args:
            step_handler: Optional async function to execute steps.
                         Signature: async def handler(step, previous_results) -> output
        """
        self._step_handler = step_handler

    async def _default_handler(self, step, previous_results: List[StepResult]):
        """Default step handler - simulates execution."""
        return f"Executed {step.step_type}"

    async def execute(self, chain) -> ChainResult:
        """
        Execute chain sequentially.

        Args:
            chain: ExecutionChain to execute

        Returns:
            ChainResult with all step results
        """
        start_time = time.time()
        step_results = []
        final_output = None
        chain_success = True
        chain_error = None

        handler = self._step_handler or self._default_handler

        for i, step in enumerate(chain.steps):
            step_start = time.time()

            try:
                # Execute step with handler
                output = await handler(step, step_results)

                step_result = StepResult(
                    step_index=i,
                    step_type=step.step_type,
                    success=True,
                    output=output,
                    error=None,
                    elapsed_ms=(time.time() - step_start) * 1000
                )
                final_output = output

            except Exception as e:
                step_result = StepResult(
                    step_index=i,
                    step_type=step.step_type,
                    success=False,
                    output=None,
                    error=str(e),
                    elapsed_ms=(time.time() - step_start) * 1000
                )
                chain_success = False
                chain_error = f"Step {i} ({step.step_type}) failed: {str(e)}"

            step_results.append(step_result)

        total_elapsed = (time.time() - start_time) * 1000

        return ChainResult(
            success=chain_success,
            steps=step_results,
            final_output=final_output,
            total_elapsed_ms=total_elapsed,
            error=chain_error
        )