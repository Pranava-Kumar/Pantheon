import asyncio
from data.upstox_client import UpstoxClient
from data.nse_client import NSEClient
from data.screener_client import ScreenerClient
from data.news_client import NewsClient
from data.context_builder import ContextBuilder
from config.settings import settings

async def test():
    upstox   = UpstoxClient(access_token='dev_token')
    nse      = NSEClient()
    screener = ScreenerClient(settings.SCREENER_EMAIL, settings.SCREENER_PASSWORD)
    news     = NewsClient()
    builder  = ContextBuilder(upstox, nse, screener, news)

    ctx = await builder.build('WIPRO', 'Wipro', 'IT', 'SIDEWAYS')

    print('Symbol:',        ctx['symbol'])
    print('Price:',         ctx['current_price'])
    print('RSI:',           ctx['technicals'].get('rsi_14'))
    print('PE:',            ctx['fundamentals'].get('pe_ratio'))
    print('FII net:',       ctx['fii_net_cash'])
    print('News count:',    ctx['news_count'])
    print('Price rows:',    len(ctx['price_summary']))
    print('PASS' if ctx['current_price'] is not None else 'FAIL')

asyncio.run(test())