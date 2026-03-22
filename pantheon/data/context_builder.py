import asyncio
from datetime import datetime
from loguru import logger

from data.upstox_client import UpstoxClient
from data.nse_client import NSEClient
from data.screener_client import ScreenerClient
from data.news_client import NewsClient
from data.indicators import compute_indicators

class ContextBuilder:
    def __init__(self, upstox: UpstoxClient, nse: NSEClient, 
                 screener: ScreenerClient, news: NewsClient):
        self.upstox = upstox
        self.nse = nse
        self.screener = screener
        self.news = news
        self.logger = logger.bind(name="ContextBuilder")

    async def build(self, symbol: str, company_name: str, 
                    sector: str, market_regime: str) -> dict:
        
        results = await asyncio.gather(
            asyncio.to_thread(self._get_price_data, symbol),
            asyncio.to_thread(self._get_nse_data, symbol),
            asyncio.to_thread(self.screener.get_fundamentals, symbol),
            asyncio.to_thread(self.news.get_news_for_symbol, symbol, company_name),
            return_exceptions=True
        )

        price_result, nse_result, fundamentals, news_items = results

        if isinstance(price_result, Exception):
            self.logger.warning(f"Error fetching price data for {symbol}: {price_result}")
            price_result = {"df": None, "technicals": {}, "current_price": None}
            
        if isinstance(nse_result, Exception):
            self.logger.warning(f"Error fetching NSE data for {symbol}: {nse_result}")
            nse_result = {}
            
        if isinstance(fundamentals, Exception):
            self.logger.warning(f"Error fetching fundamentals for {symbol}: {fundamentals}")
            fundamentals = {}
            
        if isinstance(news_items, Exception):
            self.logger.warning(f"Error fetching news for {symbol}: {news_items}")
            news_items = []

        df = price_result.get('df')
        technicals = price_result.get('technicals')
        current_price = price_result.get('current_price')

        return {
            "symbol": symbol,
            "company_name": company_name,
            "sector": sector,
            "market_regime": market_regime,
            "current_price": current_price,
            "as_of": datetime.utcnow().isoformat(),
            
            # Price history - last 10 rows
            "price_summary": df.tail(10).to_dict('records') if df is not None and not df.empty else [],
            
            "technicals": technicals or {},
            "fundamentals": fundamentals or {},
            
            "bulk_deals": nse_result.get('bulk_deals', []),
            "fii_net_cash": nse_result.get('fii_net_cash', 0.0),
            "dii_net_cash": nse_result.get('dii_net_cash', 0.0),
            
            "news": news_items[:15] if news_items else [],
            "news_count": len(news_items) if news_items else 0,
        }

    def _get_price_data(self, symbol: str) -> dict:
        try:
            instrument_key = self.upstox.get_instrument_key(symbol)
            df = self.upstox.get_historical_ohlcv(instrument_key, symbol, days=300)
            
            if df is None or df.empty:
                return {"df": None, "technicals": {}, "current_price": None}
                
            technicals = compute_indicators(df)
            current_price = float(df['close'].iloc[-1])
            
            return {
                "df": df,
                "technicals": technicals,
                "current_price": current_price
            }
        except Exception as e:
            self.logger.error(f"_get_price_data error for {symbol}: {e}")
            return {"df": None, "technicals": {}, "current_price": None}

    def _get_nse_data(self, symbol: str) -> dict:
        try:
            bulk_deals = self.nse.get_bulk_deals(symbol)
            fii_dii = self.nse.get_fii_dii_today()
            
            return {
                "bulk_deals": bulk_deals,
                "fii_net_cash": fii_dii.get('fii_net_cash', 0.0),
                "dii_net_cash": fii_dii.get('dii_net_cash', 0.0)
            }
        except Exception as e:
            self.logger.error(f"_get_nse_data error for {symbol}: {e}")
            return {"bulk_deals": [], "fii_net_cash": 0.0, "dii_net_cash": 0.0}
