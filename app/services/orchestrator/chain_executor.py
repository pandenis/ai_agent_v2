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