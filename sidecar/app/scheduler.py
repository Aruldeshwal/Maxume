"""Asyncio Token-Bucket Rate Limiter & Scheduler for Maxume Multi-Provider Cloud APIs."""

import asyncio
import time
import logging
from typing import Dict, Any, Callable, Coroutine, Optional

logger = logging.getLogger("maxume.scheduler")

class APIRateLimiter:
    def __init__(self, requests_per_minute: int, max_tokens: int, time_func: Callable[[], float] = time.monotonic):
        self.rate = requests_per_minute / 60.0  # Tokens added per second
        self.capacity = float(max_tokens)
        self.tokens = float(max_tokens)
        self.time_func = time_func
        self.last_refill = self.time_func()
        self.lock = asyncio.Lock()

    async def consume(self):
        async with self.lock:
            now = self.time_func()
            elapsed = max(0.0, now - self.last_refill)
            self.last_refill = now

            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens < 1.0:
                sleep_duration = (1.0 - self.tokens) / self.rate
                logger.info(f"[Limiter] Rate threshold hit. Sleeping {sleep_duration:.2f}s...")
                await asyncio.sleep(sleep_duration)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0

class TokenAwareScheduler:
    def __init__(self, time_func: Callable[[], float] = time.monotonic):
        self.time_func = time_func
        # Multi-provider limiters (codestandards.md §2)
        self.limiters: Dict[str, APIRateLimiter] = {
            "gemini": APIRateLimiter(requests_per_minute=15, max_tokens=15, time_func=time_func),
            "groq": APIRateLimiter(requests_per_minute=30, max_tokens=30, time_func=time_func),
        }

    async def execute_task(
        self,
        provider: str,
        task: Callable[[], Coroutine[Any, Any, Any]],
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> Any:
        limiter = self.limiters.get(provider)
        retries = 0

        while retries <= max_retries:
            if limiter:
                await limiter.consume()
            try:
                return await task()
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "ResourceExceeded" in err_str or "Too Many Requests" in err_str:
                    retries += 1
                    if retries > max_retries:
                        raise TimeoutError(f"Task failed after {max_retries} retries under rate limit scheduler for {provider}: {err_str}")
                    sleep_time = backoff_factor ** retries
                    logger.warning(f"[Scheduler] 429 detected for {provider}. Backing off {sleep_time:.2f}s (Attempt {retries}/{max_retries})...")
                    await asyncio.sleep(sleep_time)
                else:
                    raise e

        raise TimeoutError(f"Task failed after maximum retries under rate limit scheduler for {provider}")

scheduler = TokenAwareScheduler()
