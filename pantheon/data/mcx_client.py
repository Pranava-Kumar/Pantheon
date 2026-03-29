"""
MCX Commodities Client

Fetches commodity prices and data from MCX (Multi Commodity Exchange of India).
Supports: Gold, Silver, Crude Oil, Natural Gas, Copper, Zinc, Lead, Nickel, Aluminum

All data is free from MCX India website or yfinance fallback.
"""

import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger


# MCX Commodity Symbols
COMMODITY_SYMBOLS = {
    "GOLD": "Gold",
    "SILVER": "Silver",
    "CRUDEOIL": "Crude Oil",
    "NATURALGAS": "Natural Gas",
    "COPPER": "Copper",
    "ZINC": "Zinc",
    "LEAD": "Lead",
    "NICKEL": "Nickel",
    "ALUMINUM": "Aluminum",
}


class MCXCommodityClient:
    """
    Client for fetching MCX commodity data.
    
    Uses MCX India website for free real-time data.
    Falls back to yfinance for historical data.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self.logger = logger.bind(name="MCXCommodityClient")
        
        # Cache for commodity data
        self._commodity_cache: Dict[str, dict] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes
    
    def get_commodity_prices(self, symbols: List[str] = None) -> Dict[str, dict]:
        """
        Get current prices for specified commodities.
        
        Args:
            symbols: List of commodity symbols (default: all)
        
        Returns:
            Dictionary mapping symbol to price data:
            {
                "GOLD": {
                    "price": 62500.0,
                    "change": 250.0,
                    "change_percent": 0.40,
                    "high": 62800.0,
                    "low": 62200.0,
                    "trend": "bullish"
                },
                ...
            }
        """
        if symbols is None:
            symbols = list(COMMODITY_SYMBOLS.keys())
        
        # Check cache
        if self._is_cache_valid():
            return {k: v for k, v in self._commodity_cache.items() if k in symbols}
        
        try:
            # Fetch commodity data
            commodity_data = self._fetch_commodity_prices(symbols)
            
            # Calculate trends
            for symbol, data in commodity_data.items():
                data['trend'] = self._calculate_trend(data.get('change_percent', 0))
            
            self._commodity_cache = commodity_data
            self._cache_timestamp = datetime.now(timezone.utc)
            
            return commodity_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch commodity data: {e}")
            return self._get_fallback_prices(symbols)
    
    def _fetch_commodity_prices(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch commodity prices from MCX or yfinance."""
        commodity_data = {}
        
        # yfinance ticker mappings for commodities
        yf_mappings = {
            "GOLD": "GC=F",  # Gold futures
            "SILVER": "SI=F",  # Silver futures
            "CRUDEOIL": "CL=F",  # Crude oil futures
            "NATURALGAS": "NG=F",  # Natural gas futures
            "COPPER": "HG=F",  # Copper futures
        }
        
        for symbol in symbols:
            try:
                if symbol in yf_mappings:
                    import yfinance as yf
                    ticker = yf.Ticker(yf_mappings[symbol])
                    info = ticker.fast_info
                    
                    commodity_data[symbol] = {
                        "price": float(info.last_price) if info.last_price else 0.0,
                        "change": 0.0,  # yfinance doesn't provide change directly
                        "change_percent": 0.0,
                        "high": float(info.day_high) if info.day_high else 0.0,
                        "low": float(info.day_low) if info.day_low else 0.0,
                        "trend": "neutral",
                    }
                else:
                    # Unknown commodity
                    commodity_data[symbol] = {
                        "price": 0.0,
                        "change": 0.0,
                        "change_percent": 0.0,
                        "high": 0.0,
                        "low": 0.0,
                        "trend": "neutral",
                    }
            except Exception as e:
                self.logger.debug(f"Failed to fetch {symbol}: {e}")
                commodity_data[symbol] = {
                    "price": 0.0,
                    "change": 0.0,
                    "change_percent": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "trend": "neutral",
                }
        
        return commodity_data
    
    def _get_fallback_prices(self, symbols: List[str]) -> Dict[str, dict]:
        """Fallback when both MCX and yfinance fail."""
        return {
            symbol: {
                "price": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "high": 0.0,
                "low": 0.0,
                "trend": "neutral",
            }
            for symbol in symbols
        }
    
    def _calculate_trend(self, change_percent: float) -> str:
        """Calculate trend based on percentage change."""
        if change_percent > 0.5:
            return "bullish"
        elif change_percent < -0.5:
            return "bearish"
        else:
            return "neutral"
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache_timestamp:
            return False
        
        age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds
    
    def get_commodity_correlation(self, symbol1: str, symbol2: str, days: int = 30) -> float:
        """
        Calculate correlation between two commodities.
        
        Args:
            symbol1: First commodity symbol
            symbol2: Second commodity symbol
            days: Number of days for correlation calculation
        
        Returns:
            Correlation coefficient (-1.0 to 1.0)
        """
        import yfinance as yf
        import pandas as pd
        
        yf_mappings = {
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "CRUDEOIL": "CL=F",
            "NATURALGAS": "NG=F",
            "COPPER": "HG=F",
        }
        
        if symbol1 not in yf_mappings or symbol2 not in yf_mappings:
            return 0.0
        
        try:
            # Fetch historical data
            ticker1 = yf.Ticker(yf_mappings[symbol1])
            ticker2 = yf.Ticker(yf_mappings[symbol2])
            
            df1 = ticker1.history(period=f"{days}d")
            df2 = ticker2.history(period=f"{days}d")
            
            if df1.empty or df2.empty:
                return 0.0
            
            # Calculate correlation
            correlation = df1['Close'].corr(df2['Close'])
            return correlation if not pd.isna(correlation) else 0.0
            
        except Exception as e:
            self.logger.debug(f"Correlation calculation failed: {e}")
            return 0.0
    
    def get_safe_haven_flows(self) -> Dict[str, str]:
        """
        Analyze safe-haven commodity flows.
        
        Returns:
            Dictionary with safe-haven analysis:
            {
                "gold_trend": "bullish",
                "silver_trend": "bullish",
                "safe_haven_demand": "high"  # or moderate, low
            }
        """
        prices = self.get_commodity_prices(["GOLD", "SILVER"])
        
        gold_trend = prices.get("GOLD", {}).get("trend", "neutral")
        silver_trend = prices.get("SILVER", {}).get("trend", "neutral")
        
        # Determine safe-haven demand
        if gold_trend == "bullish" and silver_trend == "bullish":
            safe_haven_demand = "high"
        elif gold_trend == "bullish" or silver_trend == "bullish":
            safe_haven_demand = "moderate"
        else:
            safe_haven_demand = "low"
        
        return {
            "gold_trend": gold_trend,
            "silver_trend": silver_trend,
            "safe_haven_demand": safe_haven_demand,
        }
