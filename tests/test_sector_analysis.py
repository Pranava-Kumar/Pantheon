"""
Tests for NSE sector analysis client.
"""

import pytest
from datetime import datetime, timezone

from pantheon.data.nse_sector_client import NSESectorClient, SECTOR_INDICES


class TestNSESectorClient:
    """Test NSE sector client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create fresh sector client for each test."""
        return NSESectorClient()
    
    def test_sector_indices_defined(self):
        """Test that sector indices are properly defined."""
        assert len(SECTOR_INDICES) > 0
        assert "NIFTY_50" in SECTOR_INDICES
        assert "NIFTY_IT" in SECTOR_INDICES
        assert "NIFTY_BANK" in SECTOR_INDICES
    
    def test_get_all_sector_performance(self, client):
        """Test fetching all sector performance data."""
        sector_data = client.get_all_sector_performance()
        
        # Should return dict even if NSE is unavailable (uses fallback)
        assert isinstance(sector_data, dict)
        
        # Check structure of returned data
        if sector_data:  # May be empty if both NSE and yfinance fail
            for sector_id, data in sector_data.items():
                assert 'value' in data
                assert 'change' in data
                assert 'change_percent' in data
                assert 'trend' in data
                assert data['trend'] in ['bullish', 'bearish', 'neutral']
    
    def test_calculate_trend(self, client):
        """Test trend calculation logic."""
        # Bullish: > 0.5%
        assert client._calculate_trend(1.0) == "bullish"
        assert client._calculate_trend(0.6) == "bullish"
        
        # Bearish: < -0.5%
        assert client._calculate_trend(-1.0) == "bearish"
        assert client._calculate_trend(-0.6) == "bearish"
        
        # Neutral: between -0.5% and 0.5%
        assert client._calculate_trend(0.0) == "neutral"
        assert client._calculate_trend(0.3) == "neutral"
        assert client._calculate_trend(-0.3) == "neutral"
    
    def test_sector_rotation_signal(self, client):
        """Test sector rotation signal generation."""
        rotation = client.get_sector_rotation_signal()
        
        # Should always return valid structure
        assert isinstance(rotation, dict)
        assert 'strong_sectors' in rotation
        assert 'weak_sectors' in rotation
        assert 'rotation_signal' in rotation
        
        # Rotation signal should be valid
        assert rotation['rotation_signal'] in [
            'rotate_to_defensive',
            'rotate_to_cyclical',
            'neutral'
        ]
    
    def test_adjust_stock_score_by_sector(self, client):
        """Test stock score adjustment based on sector strength."""
        # Test with neutral sector (no adjustment)
        base_score = 0.5
        adjusted = client.adjust_stock_score_by_sector(
            symbol="INFY",
            base_score=base_score,
            sector="IT"
        )
        
        # Should return a score (may be adjusted or not depending on sector data)
        assert isinstance(adjusted, float)
        
        # Test with unknown sector (no adjustment)
        adjusted_unknown = client.adjust_stock_score_by_sector(
            symbol="UNKNOWN",
            base_score=base_score,
            sector="UnknownSector"
        )
        assert adjusted_unknown == base_score  # No adjustment for unknown sector
    
    def test_cache_validity(self, client):
        """Test cache validity checking."""
        # Initial state - no cache
        assert client._is_cache_valid() is False
        
        # After fetching data, cache should be valid
        client.get_all_sector_performance()
        assert client._is_cache_valid() is True
        
        # Cache should expire after TTL (5 minutes)
        # We can't test actual expiration without waiting, but we can verify the logic
        client._cache_timestamp = datetime.now(timezone.utc).replace(
            year=2000  # Old timestamp
        )
        assert client._is_cache_valid() is False


class TestSectorTrendCalculation:
    """Test sector trend analysis."""
    
    def test_bullish_trend_threshold(self):
        """Test bullish trend is correctly identified."""
        client = NSESectorClient()
        
        # Just above threshold
        assert client._calculate_trend(0.51) == "bullish"
        
        # Strong bullish
        assert client._calculate_trend(2.5) == "bullish"
        assert client._calculate_trend(5.0) == "bullish"
    
    def test_bearish_trend_threshold(self):
        """Test bearish trend is correctly identified."""
        client = NSESectorClient()
        
        # Just below threshold
        assert client._calculate_trend(-0.51) == "bearish"
        
        # Strong bearish
        assert client._calculate_trend(-2.5) == "bearish"
        assert client._calculate_trend(-5.0) == "bearish"
    
    def test_neutral_trend_range(self):
        """Test neutral trend range."""
        client = NSESectorClient()
        
        # Exactly at thresholds
        assert client._calculate_trend(0.5) == "neutral"
        assert client._calculate_trend(-0.5) == "neutral"
        
        # Within neutral range
        for change in [-0.4, -0.2, 0.0, 0.2, 0.4]:
            assert client._calculate_trend(change) == "neutral"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
