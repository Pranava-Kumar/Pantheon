import redis.asyncio as redis

from loguru import logger

from pantheon.config.settings import settings

# Global Redis pool
redis_client: redis.Redis = None

async def init_redis():
    """Initializes the global Redis connection pool with production-ready configuration."""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            # Connection pool configuration for production
            max_connections=50,          # Maximum concurrent connections
            socket_timeout=5.0,          # Socket timeout in seconds
            socket_connect_timeout=5.0,  # Connection timeout in seconds
            retry_on_timeout=True,       # Retry on socket timeout
            health_check_interval=30,    # Health check every 30 seconds
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
