import time
from collections import defaultdict
from fastapi import Request, Response


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: dict = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        # Keep only timestamps within window
        self.history[key] = [ts for ts in self.history[key] if ts > window_start]
        if len(self.history[key]) >= self.max_requests:
            return False
        self.history[key].append(now)
        return True


limiter = InMemoryRateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks
    if request.url.path in ("/api/v1/health", "/health"):
        return await call_next(request)
    key = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(key):
        return Response(
            content='{"detail":"Rate limit exceeded. Please slow down."}',
            status_code=429,
            media_type="application/json",
        )
    return await call_next(request)
