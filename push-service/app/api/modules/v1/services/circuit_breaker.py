"""
Circuit Breaker Pattern Implementation

Prevents cascading failures when external services (FCM, APNS, etc.) fail.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked immediately
- HALF_OPEN: Testing if service recovered, limited requests allowed

When failure threshold is reached → OPEN
After recovery timeout → HALF_OPEN
If request succeeds in HALF_OPEN → CLOSED
If request fails in HALF_OPEN → OPEN
"""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation to prevent cascading failures.

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        @breaker
        async def send_notification():
            # Your code here
            pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: tuple = (Exception,),
        name: str = "default",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exceptions to count as failures
            name: Circuit breaker identifier for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Current failure count."""
        return self._failure_count

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker '{self.name}': Attempting recovery (HALF_OPEN)")
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Retry after {self.recovery_timeout}s"
                    )

        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except self.expected_exception:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker '{self.name}': Recovery successful (CLOSED)")
                self._state = CircuitState.CLOSED

            # Reset failure count on success
            self._failure_count = 0
            self._last_failure_time = None

    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery attempt
                logger.warning(f"Circuit breaker '{self.name}': Recovery failed (OPEN)")
                self._state = CircuitState.OPEN

            elif self._failure_count >= self.failure_threshold:
                # Threshold exceeded
                logger.error(
                    f"Circuit breaker '{self.name}': Threshold exceeded "
                    f"({self._failure_count}/{self.failure_threshold}) (OPEN)"
                )
                self._state = CircuitState.OPEN
            else:
                logger.warning(
                    f"Circuit breaker '{self.name}': Failure count "
                    f"{self._failure_count}/{self.failure_threshold}"
                )

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator usage.

        @circuit_breaker
        async def my_function():
            pass
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            logger.info(f"Circuit breaker '{self.name}': Manual reset")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }
