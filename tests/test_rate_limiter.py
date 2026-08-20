import asyncio
import pytest
from app.core.rate_limiter import DistributedRateLimiter


@pytest.mark.asyncio
async def test_distributed_rate_limiter_local_acquire():
    # Test rate limiter initialization and token acquisition
    limiter = DistributedRateLimiter(rate_per_second=20, key_prefix="test:rate_limit")

    start_time = asyncio.get_event_loop().time()
    for _ in range(5):
        await limiter.acquire(1)
    duration = asyncio.get_event_loop().time() - start_time

    # 5 tokens with rate of 20/sec should acquire quickly (< 1 sec)
    assert duration < 1.5
    await limiter.close()


@pytest.mark.asyncio
async def test_distributed_rate_limiter_zero_rate_noop():
    limiter = DistributedRateLimiter(rate_per_second=0)
    await limiter.acquire(1)
    await limiter.close()
