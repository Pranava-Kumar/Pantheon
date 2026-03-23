import sys
import argparse
import statistics
from pathlib import Path

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf

from data.indicators import compute_indicators

def get_historical_prices(symbol: str, days: int) -> pd.DataFrame:
    ticker_sym = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    ticker = yf.Ticker(ticker_sym)
    
    # We fetch extra days to cover 200 trading days for the MA and indicators
    calendar_days = int((days + 200) * 1.5) + 30
    df = ticker.history(period=f"{calendar_days}d", interval="1d")
    
    if df.empty:
        return pd.DataFrame()
        
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
    
    # Prune to exactly the required sliding window scale
    return df.tail(days + 200).reset_index(drop=True)

def compute_signal_from_indicators(indicators: dict, close: float, regime: str) -> str:
    score = 0.0
    
    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi < 30: score += 0.3
        if rsi > 70: score -= 0.3
        
    macd_hist = indicators.get("macd_hist")
    if macd_hist is not None:
        if macd_hist > 0: score += 0.2
        if macd_hist < 0: score -= 0.2
        
    ema_20 = indicators.get("ema_20")
    if ema_20 is not None and close is not None:
        if close > ema_20: score += 0.2
        if close < ema_20: score -= 0.2
        
    vol_ratio = indicators.get("volume_ratio")
    if vol_ratio is not None and vol_ratio > 1.5:
        score *= 1.2
        
    thresholds = {
        "BULL":     {"buy": 0.25, "sell": -0.45},
        "SIDEWAYS": {"buy": 0.35, "sell": -0.35},
        "BEAR":     {"buy": 0.45, "sell": -0.25},
    }
    t = thresholds.get(regime, thresholds["SIDEWAYS"])
    
    if score > t["buy"]:   return "BUY"
    if score < t["sell"]:  return "SELL"
    return "HOLD"

def run_backtest(symbol: str, days: int = 180, initial_capital: float = 100000.0) -> dict:
    df = get_historical_prices(symbol, days)
    if df.empty or len(df) < 65:
        return {}
        
    # 2. Compute basic regime for the scale
    ma200 = df["close"].mean()
    last = df["close"].iloc[-1]
    
    if last > ma200 * 1.02:   
        regime = "BULL"
    elif last < ma200 * 0.98: 
        regime = "BEAR"
    else:                     
        regime = "SIDEWAYS"
    
    # 3. Slide a 200-day window
    signals = []
    
    for i in range(200, len(df) - 5):
        window = df.iloc[i-200:i].copy()
        indic = compute_indicators(window)
        current_close = df["close"].iloc[i-1]
        
        signal = compute_signal_from_indicators(indic, current_close, regime)
        
        entry_price = df["close"].iloc[i]
        exit_price = df["close"].iloc[i + 5]  # T+5 target
        
        pct_change = (exit_price - entry_price) / entry_price * 100
        actual = "BUY" if pct_change >= 2.0 else "SELL" if pct_change <= -2.0 else "HOLD"
        correct = (signal == actual) and (signal != "HOLD")
        
        signals.append({
             "date":        str(df["date"].iloc[i].date()),
             "signal":      signal,
             "actual":      actual,
             "entry":       round(entry_price, 2),
             "exit":        round(exit_price, 2),
             "pct_change":  round(pct_change, 2),
             "correct":     correct,
         })
         
    # 4. Compute statistics
    directional = [s for s in signals if s["signal"] != "HOLD"]
    correct_list = [s for s in directional if s["correct"]]
    accuracy = len(correct_list) / len(directional) if directional else 0.0
    
    pnls = [s["pct_change"] for s in directional]
    if len(pnls) >= 2:
        try:
            stdev = statistics.stdev(pnls)
            sharpe = (statistics.mean(pnls) / stdev * (252**0.5)) if stdev > 0 else 0.0
        except statistics.StatisticsError:
            sharpe = 0.0
    else:
        sharpe = 0.0
        
    buy_count = sum(1 for s in signals if s["signal"] == "BUY")
    sell_count = sum(1 for s in signals if s["signal"] == "SELL")
    hold_count = sum(1 for s in signals if s["signal"] == "HOLD")
    
    return {
       "symbol":       symbol,
       "regime":       regime,
       "days":         days,
       "total_days":   len(signals),
       "buy_signals":  buy_count,
       "sell_signals": sell_count,
       "hold_signals": hold_count,
       "accuracy":     accuracy,
       "sharpe":       sharpe,
       "signals":      signals[-10:] if len(signals) >= 10 else signals
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+", default=["WIPRO"])
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()
    
    symbols_to_run = args.symbols
    if args.symbol:
        symbols_to_run = [args.symbol]
        
    print(f"{'Symbol':<10} | {'Regime':<10} | {'Days':<5} | {'BUY':<5} | {'SELL':<5} | {'HOLD':<5} | {'Acc':<6} | {'Sharpe':<6}")
    print("-" * 75)
    
    results = []
    for sym in symbols_to_run:
        res = run_backtest(sym.upper(), args.days)
        if not res:
            print(f"{sym:<10} | {'ERROR':<10} | {args.days:<5} | {'-':<5} | {'-':<5} | {'-':<5} | {'-':<6} | {'-':<6}")
            continue
            
        acc_str = f"{res['accuracy']:.1%}"
        shr_str = f"{res['sharpe']:.2f}"
        print(f"{res['symbol']:<10} | {res['regime']:<10} | {res['total_days']:<5} | "
              f"{res['buy_signals']:<5} | {res['sell_signals']:<5} | {res['hold_signals']:<5} | "
              f"{acc_str:<6} | {shr_str:<6}")
        results.append(res)
        
    if results:
        for res in results:
            if not res["signals"]:
                continue
                
            print("\n" + "="*75)
            print(f"SAMPLE SIGNALS FOR: {res['symbol']}")
            print("="*75)
            print(f"{'Date':<12} | {'Signal':<6} | {'Actual':<6} | {'Entry':<8} | {'Exit':<8} | {'PnL%':<6} | Hit")
            
            for s in res["signals"][-5:]:
                hit = "✅" if s["correct"] else ("❌" if s["signal"] != "HOLD" else "-")
                print(f"{s['date']:<12} | {s['signal']:<6} | {s['actual']:<6} | {s['entry']:<8.2f} | {s['exit']:<8.2f} | {s['pct_change']:<6.2f} | {hit}")

if __name__ == "__main__":
    main()
