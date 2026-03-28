import json
from unittest.mock import AsyncMock, patch

import pytest

from pantheon.db.cache import cache_response, generate_cache_key


class TestCacheResponseDecorator:
    """Tests for the cache_response decorator."""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test that cached values are returned on subsequent calls."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response(expire=60)
            async def mock_func(x: int):
                nonlocal call_count
                call_count += 1
                return {"result": x * 2}

            # First call (miss)
            res1 = await mock_func(10)
            assert res1 == {"result": 20}
            assert call_count == 1
            mock_redis.get.assert_called_once()
            mock_redis.set.assert_called_once()

            # Second call (hit)
            mock_redis.get.return_value = json.dumps({"result": 20})
            res2 = await mock_func(10)
            assert res2 == {"result": 20}
            assert call_count == 1  # Still 1
            assert mock_redis.get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_no_redis(self):
        """Test graceful fallback when Redis is unavailable."""
        with patch("pantheon.db.cache.get_redis", return_value=None):
            call_count = 0

            @cache_response()
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return "data"

            assert await mock_func() == "data"
            assert await mock_func() == "data"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_empty_string(self):
        """Test that empty strings are properly cached and retrieved."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response(expire=60)
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return ""

            # First call (miss)
            res1 = await mock_func()
            assert res1 == ""
            assert call_count == 1

            # Second call (hit) - empty string should be cached
            mock_redis.get.return_value = json.dumps("")
            res2 = await mock_func()
            assert res2 == ""
            assert call_count == 1  # Still 1, cache hit

    @pytest.mark.asyncio
    async def test_cache_none_not_cached_by_default(self):
        """Test that None results are not cached by default."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response()
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return None

            assert await mock_func() is None
            assert await mock_func() is None
            assert call_count == 2  # Called twice, None not cached
            mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_none_when_enabled(self):
        """Test that None results are cached when cache_none=True."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response(cache_none=True)
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return None

            # First call (miss)
            assert await mock_func() is None
            assert call_count == 1
            mock_redis.set.assert_called_once()

            # Second call (hit)
            mock_redis.get.return_value = json.dumps(None)
            assert await mock_func() is None
            assert call_count == 1  # Still 1, cache hit

    @pytest.mark.asyncio
    async def test_cache_read_error_fallback(self):
        """Test that function executes when cache read fails and still caches result."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response()
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return "data"

            assert await mock_func() == "data"
            assert call_count == 1
            # After read error, function still executes and caches result for future
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_write_error_fallback(self):
        """Test that result is returned even when cache write fails."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.side_effect = Exception("Redis write error")

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            call_count = 0

            @cache_response()
            async def mock_func():
                nonlocal call_count
                call_count += 1
                return "data"

            assert await mock_func() == "data"
            assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_ttl_assertion(self):
        """Test that the correct TTL is passed to Redis."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            @cache_response(expire=120, key_prefix="test")
            async def mock_func(x: int):
                return x * 2

            await mock_func(5)

            # Verify TTL was set correctly
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args.kwargs["ex"] == 120

    @pytest.mark.asyncio
    async def test_cache_key_prefix(self):
        """Test that custom key prefix is used."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set = AsyncMock()

        with patch("pantheon.db.cache.get_redis", return_value=mock_redis):
            @cache_response(key_prefix="custom_prefix")
            async def mock_func():
                return "data"

            await mock_func()

            # Verify key starts with custom prefix
            call_args = mock_redis.set.call_args
            key = call_args.args[0]
            assert key.startswith("custom_prefix:")


class TestGenerateCacheKey:
    """Tests for the generate_cache_key function."""

    def test_basic_key_generation(self):
        """Test basic cache key generation."""
        key = generate_cache_key("cache", "test_func", (1, 2), {"a": 3})
        assert key.startswith("cache:")
        assert len(key) > len("cache:")

    def test_kwargs_order_independence(self):
        """Test that kwargs order doesn't affect key generation."""
        key1 = generate_cache_key("cache", "test_func", (), {"a": 1, "b": 2})
        key2 = generate_cache_key("cache", "test_func", (), {"b": 2, "a": 1})
        assert key1 == key2  # Same key regardless of order

    def test_different_args_different_keys(self):
        """Test that different arguments produce different keys."""
        key1 = generate_cache_key("cache", "test_func", (1,), {})
        key2 = generate_cache_key("cache", "test_func", (2,), {})
        assert key1 != key2

    def test_different_prefix_different_keys(self):
        """Test that different prefixes produce different keys."""
        key1 = generate_cache_key("prefix1", "test_func", (1,), {})
        key2 = generate_cache_key("prefix2", "test_func", (1,), {})
        assert key1 != key2
        assert key1.startswith("prefix1:")
        assert key2.startswith("prefix2:")

    def test_complex_args_serialization(self):
        """Test cache key generation with complex arguments."""
        key = generate_cache_key(
            "cache",
            "test_func",
            ([1, 2, 3],),
            {"data": {"nested": "value"}}
        )
        assert key.startswith("cache:")
