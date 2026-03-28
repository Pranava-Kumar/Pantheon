from fastapi import HTTPException, Request, status
import time
from collections import defaultdict
from typing import Dict, List
import asyncio

class RateLimiter:
    """
    A simple in-memory rate limiter (sliding window).
    To be replaced by Redis in a later phase.
    """
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Dictionary mapping identifier (e.g., IP) to list of request timestamps
        self.request_history: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def __call__(self, request: Request):
        # Use client host (IP) as identifier
        identifier = request.client.host if request.client else "unknown"
        now = time.time()

        async with self._lock:
            # Filter out timestamps outside the current window
            self.request_history[identifier] = [
                t for t in self.request_history[identifier]
                if now - t < self.window_seconds
            ]

            if len(self.request_history[identifier]) >= self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                    headers={"Retry-After": str(self.window_seconds)}
                )

            self.request_history[identifier].append(now)
        return True
