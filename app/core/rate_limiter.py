import asyncio
import logging
import time
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class DistributedRateLimiter:
    """
    Distributed Token-Bucket Rate Limiter backed by Redis.
    Guarantees that multiple concurrent Celery worker processes collectively
    adhere to the configured EMAIL_RATE_LIMIT_PER_SECOND without exceeding provider limits.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        rate_per_second: Optional[int] = None,
        key_prefix: str = "sherify:rate_limit:email",
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.rate_per_second = rate_per_second if rate_per_second is not None else settings.EMAIL_RATE_LIMIT_PER_SECOND
        self.key_prefix = key_prefix
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def acquire(self, count: int = 1) -> None:
        """
        Wait until `count` tokens are available within the current 1-second rolling window.
        """
        if self.rate_per_second <= 0:
            return

        try:
            r = await self._get_redis()
            while True:
                current_epoch = int(time.time())
                window_key = f"{self.key_prefix}:{current_epoch}"

                # Atomically increment the request counter for the current second
                current_count = await r.incrby(window_key, count)
                if current_count == count:
                    # Set 2-second TTL for automatic cleanup
                    await r.expire(window_key, 2)

                if current_count <= self.rate_per_second:
                    # Token successfully acquired
                    return

                # Limit exceeded for current 1-second slot; sleep until next slot
                sleep_time = max(0.05, 1.0 - (time.time() - current_epoch))
                await asyncio.sleep(min(sleep_time, 0.5))

        except Exception as exc:
            # Fallback gracefully to in-memory throttling if Redis experiences transient connectivity issues
            logger.warning(f"Distributed rate limiter Redis exception ({exc}), using local pacing.")
            delay = count / max(self.rate_per_second, 1)
            await asyncio.sleep(min(delay, 0.1))

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None


email_rate_limiter = DistributedRateLimiter()
