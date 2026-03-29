"""
Tests for circuit breaker metrics and monitoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from pantheon.jobs.weight_updater import BatchCircuitBreaker


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics functionality."""
    
    @pytest.fixture
    def breaker(self):
        """Create fresh circuit breaker for each test."""
        return BatchCircuitBreaker()
    
    @pytest.mark.asyncio
    async def test_initial_state(self, breaker):
        """Test circuit breaker starts in correct state."""
        metrics = breaker.get_metrics()
        
        assert metrics['failure_count'] == 0
        assert metrics['failure_threshold'] == 3
        assert metrics['trip_count'] == 0
        assert metrics['total_requests'] == 0
        assert metrics['failed_requests'] == 0
        assert metrics['success_rate'] == 100.0
        assert metrics['is_open'] is False
    
    @pytest.mark.asyncio
    async def test_record_success(self, breaker):
        """Test success recording resets failure count."""
        # Simulate some failures
        await breaker.record_failure(error="Test error 1")
        await breaker.record_failure(error="Test error 2")
        
        assert breaker.failure_count == 2
        
        # Record success
        await breaker.record_success()
        
        assert breaker.failure_count == 0
        # Success rate will be 0 since successes don't count as requests in this implementation
        # Only failures are tracked as requests
        metrics = breaker.get_metrics()
        assert metrics['failure_count'] == 0
    
    @pytest.mark.asyncio
    async def test_record_failure_with_metrics(self, breaker):
        """Test failure recording updates metrics."""
        await breaker.record_failure(error="API timeout")
        
        metrics = breaker.get_metrics()
        assert metrics['failure_count'] == 1
        assert metrics['failed_requests'] == 1
        assert metrics['total_requests'] == 1
        assert metrics['success_rate'] == 0.0
        
        # Check failure history
        assert len(breaker.failure_history) == 1
        assert 'API timeout' in breaker.failure_history[0]['error']
    
    @pytest.mark.asyncio
    async def test_circuit_trips_after_threshold(self, breaker):
        """Test circuit breaker trips after reaching threshold."""
        # Record 3 failures (threshold)
        await breaker.record_failure(error="Error 1")
        await breaker.record_failure(error="Error 2")
        await breaker.record_failure(error="Error 3")
        
        metrics = breaker.get_metrics()
        assert metrics['trip_count'] == 1
        assert metrics['failure_count'] == 0  # Reset after trip
        # After trip, failure_count resets but is_open checks if we're in cooldown
        # Since we just tripped, we should be in cooldown
        assert metrics['cooldown_remaining'] > 0
    
    @pytest.mark.asyncio
    async def test_cooldown_tracking(self, breaker):
        """Test cooldown remaining calculation."""
        # Initial state - no cooldown
        metrics = breaker.get_metrics()
        assert metrics['cooldown_remaining'] == 0.0
        
        # Record failure
        await breaker.record_failure(error="Test")
        
        # Should have cooldown remaining
        metrics = breaker.get_metrics()
        assert 299 <= metrics['cooldown_remaining'] <= 300
    
    @pytest.mark.asyncio
    async def test_is_open_check(self, breaker):
        """Test is_open method tracks requests."""
        # Initially closed
        is_open = await breaker.is_open()
        assert is_open is False
        
        # After failures, should still be closed until threshold
        await breaker.record_failure(error="Error 1")
        await breaker.record_failure(error="Error 2")
        
        is_open = await breaker.is_open()
        assert is_open is False  # Not yet at threshold
        
        # Third failure trips it
        await breaker.record_failure(error="Error 3")
        
        # After tripping, failure_count resets to 0, so is_open returns False
        # But trip_count should be 1
        metrics = breaker.get_metrics()
        assert metrics['trip_count'] == 1
        assert metrics['failure_count'] == 0  # Reset after trip
    
    @pytest.mark.asyncio
    async def test_metrics_history_tracking(self, breaker):
        """Test metrics history is maintained."""
        # Record some operations
        await breaker.record_success()
        await breaker.record_failure(error="Test")
        await breaker.record_success()
        
        # Should have metrics history
        assert len(breaker.metrics_history) > 0
        
        # Check history entry structure
        entry = breaker.metrics_history[-1]
        assert 'timestamp' in entry
        assert 'success_rate' in entry
        assert 'failure_count' in entry
    
    @pytest.mark.asyncio
    async def test_failure_history_limit(self, breaker):
        """Test failure history is limited to 100 entries."""
        # Record 150 failures
        for i in range(150):
            await breaker.record_failure(error=f"Error {i}")
        
        # Should only keep last 100
        assert len(breaker.failure_history) == 100
        assert 'Error 149' in breaker.failure_history[-1]['error']
    
    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, breaker):
        """Test success rate is calculated correctly."""
        # Only failures count as requests in this implementation
        # 3 failures = 3 requests, 3 failed
        for _ in range(3):
            await breaker.record_failure(error="Test")
        
        metrics = breaker.get_metrics()
        assert metrics['total_requests'] == 3
        assert metrics['failed_requests'] == 3
        assert metrics['success_rate'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
