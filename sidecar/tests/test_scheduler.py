"""Unit tests for TokenAwareScheduler and APIRateLimiter."""

import pytest
import asyncio
from unittest.mock import patch
from app.scheduler import APIRateLimiter, TokenAwareScheduler

class FakeClock:
    def __init__(self, start_time: float = 1000.0):
        self.current_time = start_time

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float):
        self.current_time += seconds

@pytest.mark.asyncio
async def test_rate_limiter_consumption():
    """Verify token consumption and refill with simulated clock."""
    clock = FakeClock(start_time=100.0)
    limiter = APIRateLimiter(requests_per_minute=60, max_tokens=2, time_func=clock.now)

    # 1. Consume initial 2 tokens immediately
    await limiter.consume()
    assert limiter.tokens == 1.0

    await limiter.consume()
    assert limiter.tokens == 0.0

    # 2. Advance clock by 1 second -> should refill 1 token (60 RPM = 1 tok/s)
    clock.advance(1.0)
    await limiter.consume()
    assert limiter.tokens == 0.0

@pytest.mark.asyncio
async def test_scheduler_exponential_backoff_and_retry():
    """Verify scheduler catches 429, backs off, and retries up to max_retries."""
    clock = FakeClock()
    sched = TokenAwareScheduler(time_func=clock.now)
    call_count = 0

    async def flaky_task():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("HTTP 429: ResourceExceeded Too Many Requests")
        return "SUCCESS_ON_ATTEMPT_3"

    with patch("asyncio.sleep", return_value=None):
        result = await sched.execute_task("gemini", flaky_task, max_retries=3, backoff_factor=1.5)
        assert result == "SUCCESS_ON_ATTEMPT_3"
        assert call_count == 3

@pytest.mark.asyncio
async def test_scheduler_max_retries_exceeded():
    """Verify scheduler raises TimeoutError when retries exceed max_retries on 429."""
    sched = TokenAwareScheduler()
    async def always_429_task():
        raise RuntimeError("429 Too Many Requests")

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(TimeoutError) as exc_info:
            await sched.execute_task("groq", always_429_task, max_retries=2)
        assert "Task failed after" in str(exc_info.value)
