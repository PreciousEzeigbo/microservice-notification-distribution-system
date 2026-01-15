"""
Retry Logic with Exponential Backoff

Automatically retries failed operations with increasing delays.
Delay formula: min(max_delay, initial_delay * (base ^ attempt))

Example:
- Attempt 1: 1s
- Attempt 2: 2s
- Attempt 3: 4s
- Attempt 4: 8s
- Attempt 5: 16s
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


class RetryHandler:
    """
    Handles retry logic with exponential backoff.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions_to_retry: tuple = (Exception,),
        exceptions_to_exclude: tuple = (),
    ):
        """
        Initialize retry handler.
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions_to_retry = exceptions_to_retry
        self.exceptions_to_exclude = exceptions_to_exclude

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for current attempt using exponential backoff.

        Formula: min(max_delay, initial_delay * (base ^ attempt))
        """
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if exception should trigger a retry."""
        # Don't retry excluded exceptions
        if isinstance(exception, self.exceptions_to_exclude):
            return False

        # Retry if exception matches retry list
        return isinstance(exception, self.exceptions_to_retry)

    async def execute(self, func: Callable, *args, context: Optional[str] = None, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            context: Optional context string for logging
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all attempts fail
        """
        last_exception = None
        context_str = f" [{context}]" if context else ""

        for attempt in range(self.max_attempts):
            try:
                logger.debug(f"Executing{context_str} - Attempt {attempt + 1}/{self.max_attempts}")
                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"Success{context_str} after {attempt + 1} attempts")

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry this exception
                if not self._should_retry(e):
                    logger.error(f"Non-retryable error{context_str}: {type(e).__name__}: {str(e)}")
                    raise

                # Check if we have more attempts
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_attempts} failed{context_str}: "
                        f"{type(e).__name__}: {str(e)} - "
                        f"Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed{context_str}: "
                        f"{type(e).__name__}: {str(e)}"
                    )

        # All attempts exhausted
        raise RetryExhaustedError(
            f"Failed after {self.max_attempts} attempts. "
            f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
        ) from last_exception

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator usage.

        @retry_handler
        async def my_function():
            pass
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.execute(func, *args, **kwargs)

        return wrapper


def create_retry_handler(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
) -> RetryHandler:
    """
    Factory function to create a retry handler with default settings.

    This is useful for creating consistent retry handlers across the application.
    """
    return RetryHandler(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        exceptions_to_retry=(Exception,),
        exceptions_to_exclude=(KeyboardInterrupt, SystemExit, asyncio.CancelledError),
    )


# Pre-configured retry handlers for common use cases
retry_aggressive = create_retry_handler(max_attempts=5, initial_delay=0.5)
retry_moderate = create_retry_handler(max_attempts=3, initial_delay=1.0)
retry_conservative = create_retry_handler(max_attempts=2, initial_delay=2.0)
