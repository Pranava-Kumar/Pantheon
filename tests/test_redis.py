import pytest
from pantheon.db.redis_client import init_redis, close_redis, get_redis
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

@pytest.mark.asyncio
async def test_redis_lifecycle():
    # Mock redis.from_url
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.close = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        await init_redis()
        client = get_redis()
        assert client is not None
        
        await close_redis()
        mock_redis.close.assert_called_once()
