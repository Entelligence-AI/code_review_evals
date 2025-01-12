import asyncio
import time
import random
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.rate_limit = requests_per_minute
        self.tokens = requests_per_minute
        self.last_updated = time.time()
        self.interval = 60.0 / requests_per_minute
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_updated
            self.tokens = min(
                self.rate_limit,
                self.tokens + time_passed * (self.rate_limit / 60.0)
            )
            self.last_updated = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) * self.interval
                await asyncio.sleep(sleep_time)
                self.tokens = 0
                self.last_updated = time.time()
            else:
                self.tokens -= 1


async def make_api_call_with_backoff(func, *args, max_retries=5, initial_delay=1):
    """Make API call with exponential backoff retry logic"""
    delay = initial_delay
    last_exception = None

    for retry in range(max_retries):
        try:
            return await asyncio.to_thread(func, *args)

        except Exception as e:
            last_exception = e

            # Check if it's a rate limit error
            if '429' in str(e):
                sleep_time = delay * (2 ** retry) + random.uniform(0, 0.1)
                logger.warning(f"Rate limit hit, retrying in {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
                continue
            else:
                # For non-rate-limit errors, raise immediately
                raise

    # If we've exhausted retries, raise the last exception
    logger.error(f"Failed after {max_retries} retries. Last error: {last_exception}")
    raise last_exception

