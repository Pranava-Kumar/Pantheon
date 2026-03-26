import redis.asyncio as redis
from pantheon.config.settings import settings
from loguru import logger

# Global Redis pool
redis_client: redis.Redis = None

async def init_redis():
    """Initializes the global Redis connection pool."""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await redis_client.ping()
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None

async def close_redis():
    """Closes the Redis connection pool."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")

def get_redis():
    """Returns the global Redis client."""
    return redis_client
