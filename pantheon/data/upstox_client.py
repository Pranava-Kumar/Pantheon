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
        
        self._instrument_map = {
            "RELIANCE": "NSE_EQ|INE002A01018",
            "TCS": "NSE_EQ|INE467B01029",
            "WIPRO": "NSE_EQ|INE075A01022",
            "INFY": "NSE_EQ|INE009A01021",
            "HDFCBANK": "NSE_EQ|INE040A01034",
            "ITC": "NSE_EQ|INE154A01025",
            "TATAMOTORS": "NSE_EQ|INE155A01022",
            "BAJFINANCE": "NSE_EQ|INE296A01024",
            "SBIN": "NSE_EQ|INE062A01020",
            "LT": "NSE_EQ|INE018A01030",
        }

    def get_historical_ohlcv(self, instrument_key: str, nse_symbol: str, days: int = 60) -> pd.DataFrame:
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
        try:
            res = self.market_quote_api.get_ltp(instrument_key=instrument_key, api_version="2.0")
            if res and res.data and instrument_key in res.data:
                return float(res.data[instrument_key].last_price)
            raise ValueError(f"No pricing data for {instrument_key}")
            
        except Exception as e:
            self.logger.error(f"Upstox LTP failed for {nse_symbol} ({instrument_key}): {str(e)}. Falling back to yfinance.")
            try:
                ticker_sym = nse_symbol if nse_symbol.startswith("^") else (nse_symbol if nse_symbol.endswith(".NS") else f"{nse_symbol}.NS")
                ticker = yf.Ticker(ticker_sym)
                return float(ticker.fast_info.last_price)
            except Exception as e2:
                self.logger.error(f"yfinance fallback failed for {nse_symbol}: {str(e2)}")
                return 0.0

    def _yfinance_fallback(self, nse_symbol: str, days: int) -> pd.DataFrame:
        try:
            ticker_sym = nse_symbol if nse_symbol.startswith("^") else (nse_symbol if nse_symbol.endswith(".NS") else f"{nse_symbol}.NS")
            ticker = yf.Ticker(ticker_sym)
            
            df = ticker.history(period=f"{days}d", interval="1d")
            
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
                    
            return df
            
        except Exception as e:
            self.logger.error(f"yfinance completely failed for {nse_symbol}: {str(e)}")
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    def get_instrument_key(self, nse_symbol: str) -> str:
        if nse_symbol in self._instrument_map:
            return self._instrument_map[nse_symbol]
            
        placeholder = f"NSE_EQ|{nse_symbol}"
        self.logger.warning(f"Instrument key not found for {nse_symbol}. Using placeholder: {placeholder}")
        return placeholder
