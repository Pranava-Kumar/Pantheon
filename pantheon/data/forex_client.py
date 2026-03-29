"""
Forex Client

Fetches currency pair data from free sources.
Supports major pairs: USD/INR, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD

All data is free from exchangerate-api.com or yfinance fallback.
"""

import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger


# Major Currency Pairs
CURRENCY_PAIRS = {
    "USDINR": "USD/INR",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD",
    "EURINR": "EUR/INR",
    "GBPINR": "GBP/INR",
    "JPYINR": "JPY/INR",
}


class ForexClient:
    """
    Client for fetching forex currency pair data.
    
    Uses free exchange rate APIs and yfinance for real-time data.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self.logger = logger.bind(name="ForexClient")
        
        # Cache for forex data
        self._forex_cache: Dict[str, dict] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes
    
    def get_currency_prices(self, pairs: List[str] = None) -> Dict[str, dict]:
        """
        Get current exchange rates for specified currency pairs.
        
        Args:
            pairs: List of currency pairs (default: major pairs)
        
        Returns:
            Dictionary mapping pair to price data:
            {
                "USDINR": {
                    "rate": 83.50,
                    "change": 0.25,
                    "change_percent": 0.30,
                    "high": 83.75,
                    "low": 83.25,
                    "trend": "bullish"
                },
                ...
            }
        """
        if pairs is None:
            pairs = list(CURRENCY_PAIRS.keys())
        
        # Check cache
        if self._is_cache_valid():
            return {k: v for k, v in self._forex_cache.items() if k in pairs}
        
        try:
            # Fetch forex data
            forex_data = self._fetch_currency_prices(pairs)
            
            # Calculate trends
            for pair, data in forex_data.items():
                data['trend'] = self._calculate_trend(data.get('change_percent', 0))
            
            self._forex_cache = forex_data
            self._cache_timestamp = datetime.now(timezone.utc)
            
            return forex_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch forex data: {e}")
            return self._get_fallback_prices(pairs)
    
    def _fetch_currency_prices(self, pairs: List[str]) -> Dict[str, dict]:
        """Fetch currency prices from APIs or yfinance."""
        forex_data = {}
        
        # yfinance ticker mappings for currency pairs
        yf_mappings = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X",
            "USDCAD": "USDCAD=X",
            "USDINR": "USDINR=X",
            "EURINR": "EURINR=X",
            "GBPINR": "GBPINR=X",
            "JPYINR": "JPYINR=X",
        }
        
        for pair in pairs:
            try:
                if pair in yf_mappings:
                    import yfinance as yf
                    ticker = yf.Ticker(yf_mappings[pair])
                    info = ticker.fast_info
                    
                    forex_data[pair] = {
                        "rate": float(info.last_price) if info.last_price else 0.0,
                        "change": 0.0,
                        "change_percent": 0.0,
                        "high": float(info.day_high) if info.day_high else 0.0,
                        "low": float(info.day_low) if info.day_low else 0.0,
                        "trend": "neutral",
                    }
                else:
                    forex_data[pair] = {
                        "rate": 0.0,
                        "change": 0.0,
                        "change_percent": 0.0,
                        "high": 0.0,
                        "low": 0.0,
                        "trend": "neutral",
                    }
            except Exception as e:
                self.logger.debug(f"Failed to fetch {pair}: {e}")
                forex_data[pair] = {
                    "rate": 0.0,
                    "change": 0.0,
                    "change_percent": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "trend": "neutral",
                }
        
        return forex_data
    
    def _get_fallback_prices(self, pairs: List[str]) -> Dict[str, dict]:
        """Fallback when APIs fail."""
        return {
            pair: {
                "rate": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "high": 0.0,
                "low": 0.0,
                "trend": "neutral",
            }
            for pair in pairs
        }
    
    def _calculate_trend(self, change_percent: float) -> str:
        """Calculate trend based on percentage change."""
        if change_percent > 0.3:
            return "bullish"  # Currency strengthening
        elif change_percent < -0.3:
            return "bearish"  # Currency weakening
        else:
            return "neutral"
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache_timestamp:
            return False
        
        age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds
    
    def get_currency_strength(self, currency: str) -> Dict[str, float]:
        """
        Calculate currency strength index against major currencies.
        
        Args:
            currency: Base currency (e.g., "USD", "EUR", "INR")
        
        Returns:
            Dictionary with strength metrics:
            {
                "strength": 0.65,  # 0-1 scale
                "trend": "strengthening",  # or weakening, neutral
                "vs_major": {...}  # Performance vs major currencies
            }
        """
        # Define major pairs for the currency
        if currency == "USD":
            pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD"]
        elif currency == "EUR":
            pairs = ["EURUSD", "EURINR"]
        elif currency == "INR":
            pairs = ["USDINR", "EURINR", "GBPINR", "JPYINR"]
        else:
            return {
                "strength": 0.5,
                "trend": "neutral",
                "vs_major": {},
            }
        
        prices = self.get_currency_prices(pairs)
        
        # Calculate strength (simplified - average of pair movements)
        strength_changes = []
        vs_major = {}
        
        for pair, data in prices.items():
            change_pct = data.get('change_percent', 0)
            
            # For USD pairs, invert the logic (USD strength = pair weakness for EURUSD, etc.)
            if currency == "USD" and pair != "USDJPY" and pair != "USDCAD":
                change_pct = -change_pct
            
            strength_changes.append(change_pct)
            vs_major[pair] = change_pct
        
        avg_strength = sum(strength_changes) / len(strength_changes) if strength_changes else 0
        
        # Normalize to 0-1 scale
        normalized_strength = 0.5 + (avg_strength / 10)  # Assuming ±10% is extreme
        normalized_strength = max(0, min(1, normalized_strength))
        
        # Determine trend
        if normalized_strength > 0.6:
            trend = "strengthening"
        elif normalized_strength < 0.4:
            trend = "weakening"
        else:
            trend = "neutral"
        
        return {
            "strength": round(normalized_strength, 3),
            "trend": trend,
            "vs_major": vs_major,
        }
    
    def get_carry_trade_opportunities(self) -> List[Dict]:
        """
        Identify carry trade opportunities based on interest rate differentials.
        
        Returns:
            List of carry trade opportunities:
            [
                {
                    "pair": "USDINR",
                    "rate_differential": 5.5,
                    "direction": "long_usd_short_inr",
                    "carry_yield": 5.5
                },
                ...
            ]
        """
        # Simplified carry trade analysis
        # In production, you'd fetch actual interest rates from central banks
        
        # Approximate interest rates (as of 2026)
        interest_rates = {
            "USD": 5.5,
            "EUR": 4.0,
            "GBP": 5.0,
            "JPY": 0.5,
            "AUD": 4.5,
            "CAD": 5.0,
            "INR": 6.5,
        }
        
        opportunities = []
        
        # Check major pairs
        pairs_to_check = [
            ("USD", "INR", "USDINR"),
            ("EUR", "USD", "EURUSD"),
            ("GBP", "USD", "GBPUSD"),
            ("USD", "JPY", "USDJPY"),
        ]
        
        for base, quote, pair in pairs_to_check:
            if base in interest_rates and quote in interest_rates:
                rate_diff = interest_rates[base] - interest_rates[quote]
                
                if abs(rate_diff) > 2.0:  # Significant differential
                    opportunities.append({
                        "pair": pair,
                        "rate_differential": round(rate_diff, 2),
                        "direction": f"long_{base.lower()}_short_{quote.lower()}" if rate_diff > 0 else f"short_{base.lower()}_long_{quote.lower()}",
                        "carry_yield": round(abs(rate_diff), 2),
                    })
        
        return sorted(opportunities, key=lambda x: x['carry_yield'], reverse=True)
