from fastapi import HTTPException, Request, status, Response
import time
from collections import OrderedDict
from typing import Dict, List, Optional
import asyncio
from loguru import logger

class RateLimiter:
    """
    A simple in-memory rate limiter (sliding window).
    To be replaced by Redis in a later phase.

    Industry best practices implemented:
    - Sliding window algorithm for accuracy
    - Periodic cleanup to prevent memory leaks
    - LRU eviction for high-traffic scenarios (O(1) with OrderedDict)
    - Logging for 429 rejections (observability)
    """
    # Maximum number of unique identifiers to track (LRU eviction)
    MAX_IDENTIFIERS = 10000

    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # OrderedDict for O(1) LRU eviction - maps identifier to list of request timestamps
        self.request_history: OrderedDict[str, List[float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _evict_lru_if_needed(self):
        """Evict oldest identifiers if we exceed MAX_IDENTIFIERS.
        
        Uses OrderedDict.popitem(last=False) for O(1) eviction per item.
        Total complexity: O(k) where k = number of items to evict.
        """
        if len(self.request_history) <= self.MAX_IDENTIFIERS:
            return
        
        # Remove oldest identifiers using O(1) popitem operation
        # popitem(last=False) removes items in FIFO order (oldest first)
        num_to_evict = len(self.request_history) - self.MAX_IDENTIFIERS
        for _ in range(num_to_evict):
            self.request_history.popitem(last=False)
        
        logger.debug(f"Rate limiter LRU eviction: removed {num_to_evict} stale identifiers")

    async def start_cleanup_task(self):
        """Start the background cleanup task. Call this during app startup."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def stop_cleanup_task(self):
        """Stop the background cleanup task. Call this during app shutdown."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _periodic_cleanup(self):
        """Periodically remove stale entries to prevent memory leak.
        
        Runs as a low-priority background task. Uses non-blocking operations
        to avoid impacting request handling performance.
        """
        while True:
            try:
                await asyncio.sleep(self.window_seconds)
                async with self._lock:
                    now = time.time()
                    # Remove stale timestamps from each key (not just fully-stale keys)
                    keys_to_remove = []
                    for key, timestamps in self.request_history.items():
                        # Keep only recent timestamps
                        self.request_history[key] = [
                            t for t in timestamps if now - t < self.window_seconds
                        ]
                        # Mark empty keys for removal
                        if not self.request_history[key]:
                            keys_to_remove.append(key)
                    # Remove empty keys
                    for key in keys_to_remove:
                        del self.request_history[key]
                    # Trigger LRU eviction after cleanup to remove excess identifiers
                    await self._evict_lru_if_needed()
            except asyncio.CancelledError:
                break
            except Exception:
                # Silently ignore cleanup errors to avoid affecting requests
                # Cleanup will retry on next interval
                pass

    async def __call__(self, request: Request):
        # Use client host (IP) as identifier
        identifier = request.client.host if request.client else "unknown"
        now = time.time()

        async with self._lock:
            # Filter out timestamps outside the current window
            # Use .get() to handle new identifiers that don't exist yet
            self.request_history[identifier] = [
                t for t in self.request_history.get(identifier, [])
                if now - t < self.window_seconds
            ]

            # Move to end to mark as recently used (for LRU)
            self.request_history.move_to_end(identifier)

            if len(self.request_history[identifier]) >= self.requests_limit:
                # Log rate limit exceeded for observability
                logger.warning(f"Rate limit exceeded for {identifier} ({self.requests_limit} req/{self.window_seconds}s)")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                    headers={"Retry-After": str(self.window_seconds)}
                )

            self.request_history[identifier].append(now)
        return True
