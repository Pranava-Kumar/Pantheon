import datetime
import requests
import pandas as pd
from loguru import logger

class NSEClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com"
        })
        self._init_session()
        
    def _init_session(self) -> None:
        try:
            self.session.get("https://www.nseindia.com", timeout=10)
            self.session.get("https://www.nseindia.com/market-data/live-equity-market", timeout=10)
            logger.info("NSE session initialized")
        except Exception:
            logger.warning("NSE session init failed, will retry on first call")
            
    def _get(self, url: str, params: dict = None) -> dict | list | None:
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code in (401, 403):
                self._init_session()
                resp = self.session.get(url, params=params, timeout=15)
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"NSEClient _get failed for {url}: {e}")
            return None

    def get_bulk_deals(self, symbol: str) -> list[dict]:
        url = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"
        params = {"type": "bulk_deals"}
        
        try:
            data = self._get(url, params=params)
            if not data or not isinstance(data, dict):
                return []
                
            items = data.get("data", [])
            if not isinstance(items, list):
                return []
                
            results = []
            for item in items:
                s = str(item.get("symbol", "")).upper()
                if s == symbol.upper():
                    results.append({
                        "date": item.get("date", ""),
                        "client_name": item.get("clientName", ""),
                        "deal_type": item.get("tradeType", ""),
                        "quantity": item.get("quantity", 0),
                        "price": item.get("price", 0.0)
                    })
            return results
        except Exception as e:
            logger.error(f"Failed to fetch bulk deals for {symbol}: {e}")
            return []

    def get_fii_dii_today(self) -> dict:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        fallback = {"fii_net_cash": 0.0, "dii_net_cash": 0.0}
        
        try:
            data = self._get(url)
            if not data or not isinstance(data, list):
                return fallback
                
            fii_net = 0.0
            dii_net = 0.0
            
            for item in data:
                cat = str(item.get("category", "")).upper()
                if "FII" in cat:
                    try:
                        fii_net = float(item.get("netValue", 0.0))
                    except (ValueError, TypeError):
                        pass
                elif "DII" in cat:
                    try:
                        dii_net = float(item.get("netValue", 0.0))
                    except (ValueError, TypeError):
                        pass
                    
            return {
                "fii_net_cash": fii_net,
                "dii_net_cash": dii_net
            }
        except Exception as e:
            logger.error(f"Failed to fetch FII/DII data: {e}")
            return fallback

    def get_market_status(self) -> str:
        try:
            data = self._get("https://www.nseindia.com/api/marketStatus")
            if not data:
                return "UNKNOWN"
            market_state = data.get("marketState", [])
            for segment in market_state:
                if segment.get("market") == "Capital Market":
                    status = segment.get("marketStatus", "").upper()
                    if "OPEN" in status:
                        return "OPEN"
                    elif "CLOSE" in status:
                        return "CLOSED"
            return "CLOSED"  # Default if Capital Market segment not found
        except Exception as e:
            self.logger.error(f"get_market_status error: {e}")
            return "UNKNOWN"

    def get_top_gainers_losers(self) -> dict:
        url = "https://www.nseindia.com/api/live-analysis-variations"
        fallback = {"gainers": [], "losers": []}
        
        try:
            g_data = self._get(url, params={"index": "gainers"})
            l_data_loosers = self._get(url, params={"index": "loosers"})
            if not l_data_loosers:
                l_data_loosers = self._get(url, params={"index": "losers"})
            
            gainers = []
            if g_data and isinstance(g_data, dict):
                companies = g_data.get("NIFTY", {}).get("data", [])
                for company in companies:
                    sym = company.get("symbol")
                    if sym:
                        gainers.append(sym)
                        
            losers = []
            if l_data_loosers and isinstance(l_data_loosers, dict):
                companies = l_data_loosers.get("NIFTY", {}).get("data", [])
                for company in companies:
                    sym = company.get("symbol")
                    if sym:
                        losers.append(sym)
                        
            return {"gainers": gainers, "losers": losers}
            
        except Exception as e:
            logger.error(f"Failed to fetch gainers/losers: {e}")
            return fallback
