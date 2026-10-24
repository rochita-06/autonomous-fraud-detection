"""Lightweight in-process rate limiting.

Good enough for a single-instance deployment or demo; swap for a
Redis-backed limiter (e.g. `slowapi` + Redis) before running multiple
backend replicas, since this state doesn't share across processes.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.headers.get('x-api-key', '')}"
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window:
            hits.popleft()

        if len(hits) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )

        hits.append(now)
        return await call_next(request)
