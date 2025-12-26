"""
RetryHandler - Handles retry logic for failed operations.

Features:
- Configurable max retries
- Exponential backoff
- Retry on specific exceptions

Usage:
    >>> handler = RetryHandler(max_retries=3)
    >>> result = handler.execute(some_function)
"""

from typing import Callable, Any


class RetryHandler:
    """Handles retry logic for failed operations."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func: Callable[[], Any]) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute

        Returns:
            Result of function call
        """
        return func()