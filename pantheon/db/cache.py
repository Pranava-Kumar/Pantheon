import functools
import hashlib
import json
from typing import Callable

from loguru import logger

from pantheon.db.redis_client import get_redis


def generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generates a stable cache key based on function arguments."""
    # Use json.dumps for consistent, compact serialization
    combined = json.dumps({"func": func_name, "args": args, "kwargs": kwargs}, sort_keys=True)
    # Use SHA256 for better collision resistance
    hash_obj = hashlib.sha256(combined.encode("utf-8"))
    return f"{prefix}:{hash_obj.hexdigest()}"


def cache_response(expire: int = 3600, key_prefix: str = "cache", cache_none: bool = False):
    """
    Decorator to cache an asynchronous function's return value in Redis.
    The function must return a JSON-serializable object.
    The wrapped function must be async.

    Args:
        expire (int): Time-to-live for the cache entry in seconds. Default: 3600.
        key_prefix (str): Prefix for the Redis key. Default: "cache".
        cache_none (bool): Whether to cache None return values. Default: False.

    Returns:
        Callable: The decorated function with caching behavior.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis = get_redis()
            if not redis:
                # If Redis is not initialized, fall back to executing the function
                logger.debug(f"Redis not available, executing {func.__name__} directly")
                return await func(*args, **kwargs)

            key = generate_cache_key(key_prefix, func.__name__, args, kwargs)

            try:
                cached_val = await redis.get(key)
                if cached_val is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return json.loads(cached_val)
            except Exception as e:
                logger.error(f"Error reading from cache: {e}")
                # Fail gracefully by falling back to the original function

            # Execute the actual function
            result = await func(*args, **kwargs)

            # Cache result (optionally including None)
            if result is not None or cache_none:
                try:
                    await redis.set(key, json.dumps(result, sort_keys=True), ex=expire)
                    logger.debug(f"Cache stored for key: {key}")
                except Exception as e:
                    logger.error(f"Error storing in cache: {e}")

            return result
        return wrapper
    return decorator
