from data.upstox_client import UpstoxClient
from data.indicators import compute_indicators

client = UpstoxClient(access_token='dev_token')
df = client._yfinance_fallback('WIPRO', 300)
print('Rows fetched:', len(df))
indicators = compute_indicators(df)
print('EMA50:', indicators['ema_50'])
print('EMA200:', indicators['ema_200'])
print('RSI:', round(indicators['rsi_14'], 2))
print('PASS' if indicators['ema_200'] is not None else 'FAIL - still not enough rows')