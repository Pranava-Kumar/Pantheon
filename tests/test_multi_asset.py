"""
Tests for multi-asset support (commodities and forex).
"""

import pytest
from datetime import datetime, timezone

from pantheon.data.mcx_client import MCXCommodityClient, COMMODITY_SYMBOLS
from pantheon.data.forex_client import ForexClient, CURRENCY_PAIRS


class TestMCXCommodityClient:
    """Test MCX commodity client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create fresh commodity client for each test."""
        return MCXCommodityClient()
    
    def test_commodity_symbols_defined(self):
        """Test that commodity symbols are properly defined."""
        assert len(COMMODITY_SYMBOLS) > 0
        assert "GOLD" in COMMODITY_SYMBOLS
        assert "SILVER" in COMMODITY_SYMBOLS
        assert "CRUDEOIL" in COMMODITY_SYMBOLS
    
    def test_get_commodity_prices(self, client):
        """Test fetching commodity prices."""
        prices = client.get_commodity_prices(["GOLD", "SILVER"])
        
        # Should return dict even if API fails (uses fallback)
        assert isinstance(prices, dict)
        
        # Check structure
        if prices:
            for symbol, data in prices.items():
                assert 'price' in data
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
    
    def test_get_safe_haven_flows(self, client):
        """Test safe-haven analysis."""
        flows = client.get_safe_haven_flows()
        
        # Should always return valid structure
        assert isinstance(flows, dict)
        assert 'gold_trend' in flows
        assert 'silver_trend' in flows
        assert 'safe_haven_demand' in flows
        
        # Safe-haven demand should be valid
        assert flows['safe_haven_demand'] in ['high', 'moderate', 'low']
    
    def test_cache_validity(self, client):
        """Test cache validity checking."""
        # Initial state - no cache
        assert client._is_cache_valid() is False
        
        # After fetching data, cache should be valid
        client.get_commodity_prices(["GOLD"])
        assert client._is_cache_valid() is True
        
        # Cache should expire after TTL (5 minutes)
        client._cache_timestamp = datetime.now(timezone.utc).replace(year=2000)
        assert client._is_cache_valid() is False


class TestForexClient:
    """Test forex client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create fresh forex client for each test."""
        return ForexClient()
    
    def test_currency_pairs_defined(self):
        """Test that currency pairs are properly defined."""
        assert len(CURRENCY_PAIRS) > 0
        assert "USDINR" in CURRENCY_PAIRS
        assert "EURUSD" in CURRENCY_PAIRS
        assert "GBPUSD" in CURRENCY_PAIRS
    
    def test_get_currency_prices(self, client):
        """Test fetching currency prices."""
        prices = client.get_currency_prices(["USDINR", "EURUSD"])
        
        # Should return dict even if API fails (uses fallback)
        assert isinstance(prices, dict)
        
        # Check structure
        if prices:
            for pair, data in prices.items():
                assert 'rate' in data
                assert 'change' in data
                assert 'change_percent' in data
                assert 'trend' in data
                assert data['trend'] in ['bullish', 'bearish', 'neutral']
    
    def test_calculate_trend(self, client):
        """Test forex trend calculation logic."""
        # Bullish: > 0.3%
        assert client._calculate_trend(1.0) == "bullish"
        assert client._calculate_trend(0.5) == "bullish"
        
        # Bearish: < -0.3%
        assert client._calculate_trend(-1.0) == "bearish"
        assert client._calculate_trend(-0.5) == "bearish"
        
        # Neutral: between -0.3% and 0.3%
        assert client._calculate_trend(0.0) == "neutral"
        assert client._calculate_trend(0.2) == "neutral"
    
    def test_get_currency_strength(self, client):
        """Test currency strength calculation."""
        strength = client.get_currency_strength("USD")
        
        # Should always return valid structure
        assert isinstance(strength, dict)
        assert 'strength' in strength
        assert 'trend' in strength
        assert 'vs_major' in strength
        
        # Strength should be 0-1
        assert 0 <= strength['strength'] <= 1
        
        # Trend should be valid
        assert strength['trend'] in ['strengthening', 'weakening', 'neutral']
    
    def test_get_carry_trade_opportunities(self, client):
        """Test carry trade opportunity identification."""
        opportunities = client.get_carry_trade_opportunities()
        
        # Should return list
        assert isinstance(opportunities, list)
        
        # Check structure if opportunities exist
        if opportunities:
            for opp in opportunities:
                assert 'pair' in opp
                assert 'rate_differential' in opp
                assert 'direction' in opp
                assert 'carry_yield' in opp
    
    def test_cache_validity(self, client):
        """Test forex cache validity checking."""
        # Initial state - no cache
        assert client._is_cache_valid() is False
        
        # After fetching data, cache should be valid
        client.get_currency_prices(["USDINR"])
        assert client._is_cache_valid() is True
        
        # Cache should expire after TTL (5 minutes)
        client._cache_timestamp = datetime.now(timezone.utc).replace(year=2000)
        assert client._is_cache_valid() is False


class TestMultiAssetIntegration:
    """Test integration between commodity and forex clients."""
    
    def test_commodity_forex_correlation(self):
        """Test that commodity and forex data can be fetched together."""
        commodity_client = MCXCommodityClient()
        forex_client = ForexClient()
        
        # Fetch both
        commodities = commodity_client.get_commodity_prices(["GOLD", "SILVER"])
        currencies = forex_client.get_currency_prices(["USDINR", "EURUSD"])
        
        # Both should return valid data structures
        assert isinstance(commodities, dict)
        assert isinstance(currencies, dict)
    
    def test_safe_haven_analysis(self):
        """Test safe-haven analysis integration."""
        commodity_client = MCXCommodityClient()
        forex_client = ForexClient()
        
        # Get safe-haven flows
        safe_haven = commodity_client.get_safe_haven_flows()
        
        # Get USD strength (safe-haven currency)
        usd_strength = forex_client.get_currency_strength("USD")
        
        # Both should be valid
        assert safe_haven['safe_haven_demand'] in ['high', 'moderate', 'low']
        assert 0 <= usd_strength['strength'] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
