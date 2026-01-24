import json
import logging
from typing import Any, Optional

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger("app")


class RedisClient:
    """
    Async Redis client wrapper for caching and rate limiting.
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[Redis] = None

    async def connect(self):
        """Establish Redis connection pool."""
        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url, max_connections=10, decode_responses=True
            )
            self._redis = Redis(connection_pool=self._pool)

            await self._redis.ping()
            logger.info(f"✓ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

        except Exception as e:
            logger.error(f"✗ Redis connection failed: {str(e)}")
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis disconnected")

    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            value = await self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {str(e)}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {str(e)}")
            return False

    # ===== JSON Operations =====

    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON value from cache."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key '{key}': {str(e)}")
                return None
        return None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Serialize and set JSON value in cache."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key '{key}': {str(e)}")
            return False

    # ===== Idempotency =====

    async def check_idempotency(
        self,
        notification_id: str,
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """
        Check if notification was already processed (idempotency).

        Returns:
            True if already processed, False if new
        """
        key = f"idempotency:{notification_id}"
        exists = await self.exists(key)

        if not exists:
            # Mark as processed
            await self.set(key, "processed", ttl)
            return False

        logger.info(f"Duplicate notification detected: {notification_id}")
        return True

    async def check_and_set_idempotency(self, key: str) -> bool:
        """
        Atomically check for idempotency and set the key if it doesn't exist.

        Returns:
            True if key already exists (duplicate), False if new
        """
        try:
            # Use Lua script for atomic check-and-set operation
            lua_script = """
            local exists = redis.call('SISMEMBER', KEYS[1], ARGV[1])
            if exists == 1 then
                return 1
            end
            redis.call('SADD', KEYS[1], ARGV[1])
            return 0
            """
            result = await self.client.eval(
                lua_script,
                1,  # Number of keys
                settings.REDIS_IDEMPOTENCY_SET,  # KEYS[1]
                key,  # ARGV[1]
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error in check_and_set_idempotency: {str(e)}")
            return False

    # ===== Rate Limiting =====

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int,
        window: int = 60,  # seconds
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User identifier
            limit: Maximum requests in window
            window: Time window in seconds

        Returns:
            (is_allowed, current_count)
        """
        key = f"rate_limit:{user_id}"

        try:
            # Increment counter
            count = await self.client.incr(key)

            # Set expiry on first request
            if count == 1:
                await self.client.expire(key, window)

            is_allowed = count <= limit

            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: {count}/{limit} in {window}s window"
                )

            return is_allowed, count

        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # Fail open (allow request on error)
            return True, 0

    # ===== Device Token Cache =====

    async def cache_invalid_token(
        self,
        token: str,
        ttl: int = 86400,  # 24 hours
    ):
        """Cache invalid device token to avoid repeated sends."""
        key = f"invalid_token:{token[:20]}"  # Use prefix to avoid huge keys
        await self.set(key, "invalid", ttl)

    async def is_token_invalid(self, token: str) -> bool:
        """Check if token is marked as invalid."""
        key = f"invalid_token:{token[:20]}"
        return await self.exists(key)

    async def are_tokens_invalid(self, tokens: list[str]) -> list[bool]:
        """Check if multiple tokens are in the invalid set."""
        try:
            async with self.client.pipeline() as pipe:
                for token in tokens:
                    pipe.sismember(settings.REDIS_INVALID_TOKEN_SET, token)
                results = await pipe.execute()
            return [bool(r) for r in results]
        except Exception as e:
            logger.error(f"Error checking multiple invalid tokens: {str(e)}")
            return [False] * len(tokens)

    async def cache_invalid_tokens(self, tokens: list[str]) -> bool:
        """Cache multiple invalid tokens in a set."""
        if not tokens:
            return True
        try:
            await self.client.sadd(settings.REDIS_INVALID_TOKEN_SET, *tokens)
            logger.debug(f"Cached {len(tokens)} invalid tokens.")
            return True
        except Exception as e:
            logger.error(f"Error caching multiple invalid tokens: {str(e)}")
            return False

    # ===== Health Check =====

    async def health_check(self) -> dict:
        """Check Redis health and return stats."""
        try:
            start_time = await self._get_time()
            await self.client.ping()
            end_time = await self._get_time()
            latency = (end_time - start_time) * 1000  # ms

            info = await self.client.info()

            return {
                "status": "up",
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
            }
        except Exception as e:
            return {"status": "down", "error": str(e)}

    async def _get_time(self) -> float:
        """Get current time for latency measurement."""
        import time

        return time.time()


# Global Redis client instance
redis_client = RedisClient()
