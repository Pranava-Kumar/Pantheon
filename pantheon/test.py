import yfinance as yf
t = yf.Ticker('ONGC.NS')
print(t.fast_info.last_price)