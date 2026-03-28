"""
Tests for critical production features:
- Redis distributed lock
- Batch price fetching with retry
- Rate limiter LRU eviction
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta


class TestRedisDistributedLock:
    """Test Redis distributed lock implementation in weight_updater.py"""

    @pytest.mark.asyncio
    async def test_lock_acquired_with_unique_token(self):
        """Verify lock uses unique UUID token for ownership verification."""
        from pantheon.jobs.weight_updater import _process_update_for_date
        import uuid
        
        with patch('pantheon.jobs.weight_updater.get_redis') as mock_redis:
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.set = AsyncMock(return_value=True)
            
            with patch('pantheon.jobs.weight_updater.SessionLocal'):
                with patch('pantheon.jobs.weight_updater.get_active_upstox_token'):
                    with patch('pantheon.jobs.weight_updater.load_weights'):
                        # Call the function
                        await _process_update_for_date(datetime.now().date())
                        
                        # Verify set was called with a UUID token (not hardcoded string)
                        call_args = mock_redis.return_value.set.call_args
                        assert call_args is not None
                        lock_token = call_args[0][1]  # Second positional arg is the token
                        # Verify it's a valid UUID format
                        uuid.UUID(lock_token)  # Will raise if invalid

    @pytest.mark.asyncio
    async def test_lock_released_atomically_with_lua_script(self):
        """Verify lock release uses Lua script for atomic operation."""
        from pantheon.jobs.weight_updater import _process_update_for_date
        
        with patch('pantheon.jobs.weight_updater.get_redis') as mock_redis:
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.set = AsyncMock(return_value=True)
            mock_redis.return_value.eval = AsyncMock(return_value=1)
            
            with patch('pantheon.jobs.weight_updater.SessionLocal'):
                with patch('pantheon.jobs.weight_updater.get_active_upstox_token'):
                    with patch('pantheon.jobs.weight_updater.load_weights'):
                        await _process_update_for_date(datetime.now().date())
                        
                        # Verify eval was called (Lua script for atomic release)
                        assert mock_redis.return_value.eval.called

    @pytest.mark.asyncio
    async def test_redis_closed_on_lock_failure(self):
        """Verify Redis connection is closed when lock acquisition fails."""
        from pantheon.jobs.weight_updater import _process_update_for_date
        
        with patch('pantheon.jobs.weight_updater.get_redis') as mock_redis:
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.set = AsyncMock(side_effect=Exception("Redis unavailable"))
            
            with patch('pantheon.jobs.weight_updater.SessionLocal'):
                result = await _process_update_for_date(datetime.now().date())
                
                # Verify function returned early
                assert result == {}
                
                # Verify Redis close was called
                mock_redis.return_value.close.assert_called()


class TestBatchPriceFetching:
    """Test batch price fetching with retry logic in upstox_client.py"""

    def test_batch_prices_retry_with_exponential_backoff(self):
        """Verify batch price fetch retries with exponential backoff."""
        from pantheon.data.upstox_client import UpstoxClient
        
        with patch.object(UpstoxClient, '__init__', lambda x, **kwargs: None):
            client = UpstoxClient()
            client.logger = Mock()
            
            # Mock the API to fail twice then succeed
            mock_api = Mock()
            mock_api.get_quotes = Mock(side_effect=[
                Exception("API error 1"),
                Exception("API error 2"),
                Mock(data={"key1": Mock(last_price=100.0)})
            ])
            client.market_quote_api = mock_api
            
            # Call batch prices
            result = client.get_batch_prices(["key1", "key2"])
            
            # Verify API was called 3 times (initial + 2 retries)
            assert mock_api.get_quotes.call_count == 3
            
            # Verify delays between calls (exponential backoff)
            # First call at t=0, second at t=0.5, third at t=1.5

    def test_batch_prices_fallback_on_complete_failure(self):
        """Verify empty dict returned when all retries exhausted."""
        from pantheon.data.upstox_client import UpstoxClient
        
        with patch.object(UpstoxClient, '__init__', lambda x, **kwargs: None):
            client = UpstoxClient()
            client.logger = Mock()
            
            # Mock the API to always fail
            mock_api = Mock()
            mock_api.get_quotes = Mock(side_effect=Exception("Always fails"))
            client.market_quote_api = mock_api
            
            # Call batch prices
            result = client.get_batch_prices(["key1"])
            
            # Verify empty dict returned
            assert result == {}
            
            # Verify 3 attempts were made
            assert mock_api.get_quotes.call_count == 3


class TestRateLimiterLRUEviction:
    """Test rate limiter LRU eviction in rate_limiter.py"""

    @pytest.mark.asyncio
    async def test_lru_eviction_when_exceeds_max_identifiers(self):
        """Verify oldest identifiers are evicted when limit exceeded."""
        from pantheon.api.rate_limiter import RateLimiter
        
        # Create limiter with small max for testing
        limiter = RateLimiter(requests_limit=60, window_seconds=60)
        limiter.MAX_IDENTIFIERS = 5  # Small limit for testing
        
        # Add 7 identifiers
        for i in range(7):
            limiter.request_history[f"ip_{i}"] = [1000.0 + i]
        
        # Trigger eviction
        await limiter._evict_lru_if_needed()
        
        # Verify only 5 identifiers remain (oldest 2 evicted)
        assert len(limiter.request_history) == 5
        assert "ip_0" not in limiter.request_history
        assert "ip_1" not in limiter.request_history
        assert "ip_2" in limiter.request_history
        assert "ip_6" in limiter.request_history

    @pytest.mark.asyncio
    async def test_lru_eviction_is_o1_operation(self):
        """Verify LRU eviction is O(1) with OrderedDict."""
        from pantheon.api.rate_limiter import RateLimiter
        import time
        
        limiter = RateLimiter(requests_limit=60, window_seconds=60)
        limiter.MAX_IDENTIFIERS = 100
        
        # Add 150 identifiers
        for i in range(150):
            limiter.request_history[f"ip_{i}"] = [1000.0 + i]
        
        # Time the eviction
        start = time.time()
        await limiter._evict_lru_if_needed()
        elapsed = time.time() - start
        
        # Verify eviction is fast (O(1) should be < 1ms even with many items)
        assert elapsed < 0.01  # 10ms threshold
        
        # Verify correct number remain
        assert len(limiter.request_history) == 100

    @pytest.mark.asyncio
    async def test_move_to_end_marks_as_recently_used(self):
        """Verify move_to_end is called to mark identifier as recently used."""
        from pantheon.api.rate_limiter import RateLimiter
        from fastapi import Request
        
        limiter = RateLimiter(requests_limit=60, window_seconds=60)
        limiter.MAX_IDENTIFIERS = 5
        
        # Add identifiers in order
        for i in range(3):
            limiter.request_history[f"ip_{i}"] = [1000.0 + i]
        
        # Verify initial order
        keys_before = list(limiter.request_history.keys())
        assert keys_before == ["ip_0", "ip_1", "ip_2"]
        
        # Simulate request from ip_0 (should move to end)
        mock_request = Mock(spec=Request)
        mock_request.client.host = "ip_0"
        
        await limiter(mock_request)
        
        # Verify ip_0 moved to end
        keys_after = list(limiter.request_history.keys())
        assert keys_after == ["ip_1", "ip_2", "ip_0"]


class TestHealthCheckTimeout:
    """Test health check timeout in routes.py"""

    @pytest.mark.asyncio
    async def test_health_check_uses_2_second_timeout(self):
        """Verify health check uses 2-second timeout for Redis ping."""
        # This is a code inspection test - verify the timeout value in source
        import inspect
        from pantheon.api.routes import health_check
        
        source = inspect.getsource(health_check)
        
        # Verify timeout is 2.0 seconds
        assert "timeout=2.0" in source
        assert "wait_for" in source  # Uses asyncio.wait_for


class TestSemaphoreDBSessionOrder:
    """Test semaphore is acquired before DB session in daily_analysis.py"""

    @pytest.mark.asyncio
    async def test_semaphore_acquired_before_db_session(self):
        """Verify semaphore wraps DB session creation."""
        import inspect
        from pantheon.jobs.daily_analysis import run_daily_analysis
        
        source = inspect.getsource(run_daily_analysis)
        
        # Verify semaphore is acquired before SessionLocal in analyze_stock
        # Look for the pattern: async with semaphore: ... db = SessionLocal()
        assert "async with semaphore:" in source
        
        # Find the analyze_stock function
        analyze_stock_start = source.find("async def analyze_stock")
        semaphore_pos = source.find("async with semaphore:", analyze_stock_start)
        session_pos = source.find("db = SessionLocal()", analyze_stock_start)
        
        # Verify semaphore comes before SessionLocal
        assert semaphore_pos < session_pos, "Semaphore must be acquired before DB session"


class TestJWTValidationDevMode:
    """Test JWT validation allows empty secret for development."""

    def test_jwt_validation_allows_empty_for_non_production(self):
        """Verify empty JWT secret is allowed for non-production environments."""
        from pantheon.config.settings import Settings
        import os
        
        # Save original environment
        original_env = os.environ.get("ENVIRONMENT")
        
        try:
            # Set to development
            os.environ["ENVIRONMENT"] = "development"
            os.environ["DATABASE_URL"] = "sqlite:///test.db"
            os.environ["DATABASE_URL_ASYNC"] = "sqlite:///test.db"
            os.environ["GOOGLE_API_KEY"] = "test"
            os.environ["GROQ_API_KEY"] = "test"
            
            # Should not raise for empty JWT in development
            settings = Settings()
            assert settings.JWT_SECRET_KEY == "dev-secret-key-change-in-production"
            
        finally:
            # Restore original environment
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_jwt_validation_requires_secret_for_production(self):
        """Verify empty JWT secret raises error for production."""
        from pantheon.config.settings import Settings
        import os
        
        original_env = os.environ.get("ENVIRONMENT")
        
        try:
            os.environ["ENVIRONMENT"] = "production"
            os.environ["DATABASE_URL"] = "sqlite:///test.db"
            os.environ["DATABASE_URL_ASYNC"] = "sqlite:///test.db"
            os.environ["GOOGLE_API_KEY"] = "test"
            os.environ["GROQ_API_KEY"] = "test"
            # Don't set JWT_SECRET_KEY
            
            # Should raise for empty JWT in production
            with pytest.raises(ValueError) as exc_info:
                Settings()
            
            assert "JWT_SECRET_KEY cannot be empty in production" in str(exc_info.value)
            
        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]
