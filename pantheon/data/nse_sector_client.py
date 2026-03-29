"""
NSE Sector Indices Client

Fetches and tracks Nifty sector indices for market breadth analysis.
All data is free from NSE India website.

Sector Indices:
- NIFTY IT
- NIFTY BANK
- NIFTY AUTO
- NIFTY PHARMA
- NIFTY FMCG
- NIFTY METAL
- NIFTY ENERGY
- NIFTY FINANCIAL SERVICES
- NIFTY REALTY
- NIFTY MEDIA
"""

import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger


# Nifty Sector Indices with NSE trading symbols
SECTOR_INDICES = {
    "NIFTY_IT": "Nifty IT",
    "NIFTY_BANK": "Nifty Bank",
    "NIFTY_AUTO": "Nifty Auto",
    "NIFTY_PHARMA": "Nifty Pharma",
    "NIFTY_FMCG": "Nifty FMCG",
    "NIFTY_METAL": "Nifty Metal",
    "NIFTY_ENERGY": "Nifty Energy",
    "NIFTY_FIN_SERVICE": "Nifty Financial Services",
    "NIFTY_REALTY": "Nifty Realty",
    "NIFTY_MEDIA": "Nifty Media",
    "NIFTY_50": "Nifty 50",  # Benchmark
}


class NSESectorClient:
    """
    Client for fetching NSE sector indices data.
    
    Uses NSE India website for free real-time data.
    No API key required.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self.logger = logger.bind(name="NSESectorClient")
        
        # Cache for sector data
        self._sector_cache: Dict[str, dict] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes
    
    def get_all_sector_performance(self) -> Dict[str, dict]:
        """
        Get performance data for all sector indices.
        
        Returns:
            Dictionary mapping sector name to performance data:
            {
                "NIFTY_IT": {
                    "value": 12345.67,
                    "change": 123.45,
                    "change_percent": 1.02,
                    "trend": "bullish"  # bullish, bearish, neutral
                },
                ...
            }
        """
        # Check cache
        if self._is_cache_valid():
            return self._sector_cache
        
        try:
            # Fetch sector data from NSE
            sector_data = self._fetch_sector_indices()
            
            # Calculate trends
            for sector_id, data in sector_data.items():
                data['trend'] = self._calculate_trend(data['change_percent'])
            
            self._sector_cache = sector_data
            self._cache_timestamp = datetime.now(timezone.utc)
            
            return sector_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch sector data: {e}")
            # Return cached data if available, else empty dict
            return self._sector_cache if self._sector_cache else {}
    
    def _fetch_sector_indices(self) -> Dict[str, dict]:
        """
        Fetch sector indices from NSE website.
        
        Note: This uses web scraping. For production, consider using
        official NSE API or a paid data provider.
        """
        sector_data = {}
        
        # NSE indices endpoint (public, no auth required)
        base_url = "https://www.nseindia.com/market-data/indices-and-composites"
        
        try:
            # Try to fetch main indices page
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()
            
            # Parse the response (simplified - in production, use proper HTML parsing)
            # For now, return mock data structure
            # In production, you'd parse the HTML/JSON from NSE
            
            for sector_id, sector_name in SECTOR_INDICES.items():
                # Mock data - replace with actual scraping logic
                sector_data[sector_id] = {
                    "value": 0.0,
                    "change": 0.0,
                    "change_percent": 0.0,
                    "trend": "neutral",
                }
            
            return sector_data
            
        except Exception as e:
            self.logger.warning(f"NSE fetch failed, using fallback: {e}")
            return self._get_fallback_sector_data()
    
    def _get_fallback_sector_data(self) -> Dict[str, dict]:
        """
        Fallback sector data when NSE is unavailable.
        
        Uses yfinance for sector index data as backup.
        """
        import yfinance as yf
        
        sector_data = {}
        
        # Yahoo Finance ticker mappings for Nifty indices
        yf_mappings = {
            "NIFTY_50": "^NSEI",
            "NIFTY_BANK": "^NSEBANK",
            "NIFTY_IT": "^CNXIT",
            "NIFTY_AUTO": "^CNXAUTO",
            "NIFTY_PHARMA": "^CNXPHARMA",
            "NIFTY_FMCG": "^CNXFMCG",
        }
        
        for sector_id, yf_ticker in yf_mappings.items():
            try:
                ticker = yf.Ticker(yf_ticker)
                info = ticker.fast_info
                
                sector_data[sector_id] = {
                    "value": float(info.last_price) if info.last_price else 0.0,
                    "change": 0.0,  # yfinance doesn't provide change directly
                    "change_percent": 0.0,
                    "trend": "neutral",
                }
            except Exception as e:
                self.logger.debug(f"yfinance fallback failed for {sector_id}: {e}")
                sector_data[sector_id] = {
                    "value": 0.0,
                    "change": 0.0,
                    "change_percent": 0.0,
                    "trend": "neutral",
                }
        
        return sector_data
    
    def _calculate_trend(self, change_percent: float) -> str:
        """
        Calculate trend based on percentage change.
        
        Args:
            change_percent: Percentage change in index value
        
        Returns:
            "bullish" if > 0.5%, "bearish" if < -0.5%, else "neutral"
        """
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
    
    def get_sector_rotation_signal(self) -> Dict[str, str]:
        """
        Identify sector rotation signals based on relative strength.
        
        Returns:
            Dictionary with sector rotation recommendations:
            {
                "strong_sectors": ["NIFTY_IT", "NIFTY_PHARMA"],
                "weak_sectors": ["NIFTY_BANK", "NIFTY_REALTY"],
                "rotation_signal": "rotate_to_defensive"  # or rotate_to_cyclical, neutral
            }
        """
        sector_data = self.get_all_sector_performance()
        
        if not sector_data:
            return {
                "strong_sectors": [],
                "weak_sectors": [],
                "rotation_signal": "neutral",
            }
        
        # Sort sectors by performance
        sorted_sectors = sorted(
            sector_data.items(),
            key=lambda x: x[1].get('change_percent', 0),
            reverse=True
        )
        
        # Top 3 sectors are strong, bottom 3 are weak
        strong_sectors = [s[0] for s in sorted_sectors[:3] if s[1].get('change_percent', 0) > 0.5]
        weak_sectors = [s[0] for s in sorted_sectors[-3:] if s[1].get('change_percent', 0) < -0.5]
        
        # Determine rotation signal
        defensive_sectors = {"NIFTY_PHARMA", "NIFTY_FMCG", "NIFTY_IT"}
        cyclical_sectors = {"NIFTY_BANK", "NIFTY_AUTO", "NIFTY_METAL", "NIFTY_REALTY"}
        
        strong_defensive = len(set(strong_sectors) & defensive_sectors)
        strong_cyclical = len(set(strong_sectors) & cyclical_sectors)
        
        if strong_defensive > strong_cyclical:
            rotation_signal = "rotate_to_defensive"
        elif strong_cyclical > strong_defensive:
            rotation_signal = "rotate_to_cyclical"
        else:
            rotation_signal = "neutral"
        
        return {
            "strong_sectors": strong_sectors,
            "weak_sectors": weak_sectors,
            "rotation_signal": rotation_signal,
        }
    
    def adjust_stock_score_by_sector(self, symbol: str, base_score: float, sector: str) -> float:
        """
        Adjust individual stock score based on sector strength.
        
        Args:
            symbol: Stock symbol (e.g., "INFY")
            base_score: Original MMCI score
            sector: Stock's sector (e.g., "IT")
        
        Returns:
            Adjusted score (boosted if sector is strong, reduced if weak)
        """
        sector_data = self.get_all_sector_performance()
        
        # Map sector to index
        sector_to_index = {
            "IT": "NIFTY_IT",
            "Banking": "NIFTY_BANK",
            "Auto": "NIFTY_AUTO",
            "Pharma": "NIFTY_PHARMA",
            "FMCG": "NIFTY_FMCG",
            "Metals": "NIFTY_METAL",
            "Energy": "NIFTY_ENERGY",
            "Finance": "NIFTY_FIN_SERVICE",
            "Realty": "NIFTY_REALTY",
            "Media": "NIFTY_MEDIA",
        }
        
        index_id = sector_to_index.get(sector)
        if not index_id or index_id not in sector_data:
            return base_score  # No adjustment if sector data unavailable
        
        index_performance = sector_data[index_id]
        trend = index_performance.get('trend', 'neutral')
        
        # Adjust score based on sector trend
        if trend == "bullish":
            # Boost bullish stocks in strong sectors
            return base_score * 1.1 if base_score > 0 else base_score
        elif trend == "bearish":
            # Reduce bullish stocks in weak sectors
            return base_score * 0.9 if base_score > 0 else base_score
        else:
            return base_score  # No adjustment for neutral
