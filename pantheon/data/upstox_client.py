import datetime
import pandas as pd
import yfinance as yf
from loguru import logger
import upstox_client

class UpstoxClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = access_token
        
        # Initialize HistoryV3Api (or HistoryApi as fallback)
        try:
            self.history_api = upstox_client.HistoryV3Api(upstox_client.ApiClient(self.configuration))
        except AttributeError:
            self.history_api = upstox_client.HistoryApi(upstox_client.ApiClient(self.configuration))
            
        self.market_quote_api = upstox_client.MarketQuoteApi(upstox_client.ApiClient(self.configuration))
        
        self.logger = logger.bind(name="UpstoxClient")
        
        self._instrument_map = {}
        self._load_instruments()

    def _load_instruments(self) -> None:
        import os
        import json
        cache_file = "upstox_instruments.json"
        
        if os.path.exists(cache_file):
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.datetime.now() - modified).days < 1:
                try:
                    with open(cache_file, "r") as f:
                        self._instrument_map = json.load(f)
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to read instrument cache: {e}")
                    
        self.logger.info("Downloading master instrument list from Upstox (cached for 24h)...")
        try:
            import requests
            import gzip
            
            url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
            resp = requests.get(url, timeout=30)
            data = json.loads(gzip.decompress(resp.content))
            
            for item in data:
                if item.get("segment") == "NSE_EQ":
                    name = item.get("name")
                    ts = item.get("trading_symbol", "").split('-')[0]
                    ikey = item.get("instrument_key")
                    
                    if name: self._instrument_map[name] = ikey
                    if ts:   self._instrument_map[ts]   = ikey
                    
            # Index fallbacks map locally
            nifty_item = next((item for item in data if item.get("name") == "Nifty 50" and item.get("segment") == "NSE_INDEX"), None)
            if nifty_item:
                self._instrument_map["^NSEI"] = nifty_item["instrument_key"]
            else:
                self._instrument_map["^NSEI"] = "NSE_INDEX|Nifty 50"
                
            with open(cache_file, "w") as f:
                json.dump(self._instrument_map, f)
                
            self.logger.info(f"Loaded {len(self._instrument_map)} NSE instruments.")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Upstox instruments: {e}")

    def get_historical_ohlcv(self, instrument_key: str, nse_symbol: str, days: int = 300) -> pd.DataFrame:
        if instrument_key.startswith("YFINANCE_ONLY"):
            self.logger.debug(f"Direct fallback to yfinance for {nse_symbol} (unmapped).")
            return self._yfinance_fallback(nse_symbol, days)
            
        try:
            today = datetime.datetime.now()
            from_date_obj = today - datetime.timedelta(days=days)
            to_date = today.strftime("%Y-%m-%d")
            from_date = from_date_obj.strftime("%Y-%m-%d")
            
            try:
                res = self.history_api.get_historical_candle_data1(instrument_key, "days", "1", to_date, from_date)
            except Exception:
                res = self.history_api.get_historical_candle_data1(
                    instrument_key=instrument_key,
                    interval="day",
                    to_date=to_date,
                    from_date=from_date,
                    api_version="2.0"
                )
            
            if not res or not res.data or not res.data.candles:
                raise ValueError("No data returned from Upstox")
                
            records = res.data.candles
            df = pd.DataFrame(records, columns=["date", "open", "high", "low", "close", "volume", "oi"])
            df["date"] = pd.to_datetime(df["date"])
            
            df = df.drop(columns=["oi"], errors="ignore")
            
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col])
                
            df = df.sort_values("date", ascending=True).reset_index(drop=True)
            return df
            
        except Exception as e:
            self.logger.error(f"Upstox API failed for {nse_symbol} ({instrument_key}): {str(e)}. Falling back to yfinance.")
            return self._yfinance_fallback(nse_symbol, days)

    def get_nifty50_history(self, days: int = 250) -> pd.DataFrame:
        instrument_key = "NSE_INDEX|Nifty 50"
        nse_symbol = "^NSEI"
        
        df = self.get_historical_ohlcv(instrument_key=instrument_key, nse_symbol=nse_symbol, days=days)
        if df.empty:
            return pd.DataFrame(columns=["date", "close"])
            
        return df[["date", "close"]]

    def get_current_price(self, instrument_key: str, nse_symbol: str) -> float:
        if instrument_key.startswith("YFINANCE_ONLY"):
            return self._yfinance_current_fallback(nse_symbol)
            
        try:
            res = self.market_quote_api.get_ltp(instrument_key=instrument_key, api_version="2.0")
            if res and res.data and instrument_key in res.data:
                return float(res.data[instrument_key].last_price)
            raise ValueError(f"No pricing data for {instrument_key}")
            
        except Exception as e:
            self.logger.error(f"Upstox LTP failed for {nse_symbol} ({instrument_key}): {str(e)}. Falling back to yfinance.")
            return self._yfinance_current_fallback(nse_symbol)
            
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validates if a symbol exists either in Upstox (NSE) or via yfinance (Global).
        """
        if symbol in self._instrument_map:
            return True
            
        # Fallback to yfinance validation
        for s in [f"{symbol}.NS", symbol]:
            try:
                ticker = yf.Ticker(s)
                df = ticker.history(period="1d")
                if not df.empty:
                    return True
            except Exception:
                continue
        return False

    def _yfinance_current_fallback(self, nse_symbol: str) -> float:
        try:
            # Try cascading: symbol.NS then symbol
            for s in [f"{nse_symbol}.NS", nse_symbol]:
                try:
                    ticker = yf.Ticker(s)
                    price = float(ticker.fast_info.last_price)
                    if price > 0: return price
                except Exception:
                    continue
            return 0.0
        except Exception as e2:
            self.logger.error(f"yfinance fallback failed for {nse_symbol}: {str(e2)}")
            return 0.0

    def _yfinance_fallback(self, nse_symbol: str, days: int) -> pd.DataFrame:
        try:
            df = pd.DataFrame()
            # Try cascading: symbol.NS then symbol
            for s in [f"{nse_symbol}.NS", nse_symbol]:
                try:
                    ticker = yf.Ticker(s)
                    # Multiply by 1.5 to convert trading days to calendar days
                    # Add 60 buffer for holidays. Minimum 400 to guarantee EMA200.
                    calendar_days = max(int(days * 1.5) + 60, 400)
                    df = ticker.history(period=f"{calendar_days}d", interval="1d")
                    if not df.empty: break
                except Exception:
                    continue
            
            if df.empty:
                return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
                
            df = df.reset_index()
            
            rename_map = {
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }
            df = df.rename(columns=rename_map)
            
            cols = ["date", "open", "high", "low", "close", "volume"]
            df = df[[c for c in cols if c in df.columns]]
            
            for c in cols:
                if c not in df.columns:
                    df[c] = 0.0 if c != "date" else pd.NaT
                    
            return df.tail(days).reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"yfinance completely failed for {nse_symbol}: {str(e)}")
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    def get_instrument_key(self, nse_symbol: str) -> str:
        if nse_symbol in self._instrument_map:
            return self._instrument_map[nse_symbol]
            
        # Return a silent flag enforcing direct yfinance override 
        # to block API traces and noisy ERROR logging dumps
        return f"YFINANCE_ONLY|{nse_symbol}"
