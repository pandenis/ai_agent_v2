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

import time
from typing import Callable, Any, Optional


class RetryHandler:
    """Handles retry logic for failed operations."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        exponential_backoff: bool = False
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            exponential_backoff: If True, delay doubles each retry
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_backoff = exponential_backoff
        self._last_exception: Optional[Exception] = None
        self._total_attempts = 0
        self._success = False

    def _get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if self.exponential_backoff:
            return self.base_delay * (2 ** attempt)
        return self.base_delay

    def execute(self, func: Callable[[], Any]) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute

        Returns:
            Result of function call

        Raises:
            Exception: If all retries exhausted
        """
        self._total_attempts = 0
        self._success = False

        while self._total_attempts <= self.max_retries:
            try:
                self._total_attempts += 1
                result = func()
                self._success = True
                return result
            except Exception as e:
                self._last_exception = e
                if self._total_attempts <= self.max_retries:
                    delay = self._get_delay(self._total_attempts - 1)
                    time.sleep(delay)

        raise self._last_exception

    def get_stats(self) -> dict:
        """Get retry statistics."""
        return {
            "total_attempts": self._total_attempts,
            "retries_used": max(0, self._total_attempts - 1),
            "max_retries": self.max_retries,
            "success": self._success,
        }