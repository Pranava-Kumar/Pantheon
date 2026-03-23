import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from loguru import logger

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from data.upstox_client import UpstoxClient
from data.nse_client import NSEClient
from data.screener_client import ScreenerClient
from data.news_client import NewsClient
from data.context_builder import ContextBuilder
from agents.graph import build_graph
from config import load_watchlist

# ANSI Escape Codes for formatting
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

async def main(symbols: list[str] | None):
    if not symbols:
        symbols = [item["symbol"] for item in load_watchlist()]
        
    print("Initializing clients...")
    upstox = UpstoxClient(access_token="dev_token")
    nse = NSEClient()
    screener = ScreenerClient(settings.SCREENER_EMAIL, settings.SCREENER_PASSWORD)
    news = NewsClient()
    builder = ContextBuilder(upstox, nse, screener, news)

    print("Detecting market regime...")
    nifty_df = upstox.get_nifty50_history(days=250)
    
    if nifty_df is not None and not nifty_df.empty:
        # Calculate 200-day moving average
        ma200 = nifty_df["close"].tail(200).mean()
        last = nifty_df["close"].iloc[-1]
        
        if last > ma200 * 1.02:
            regime = "BULL"
        elif last < ma200 * 0.98:
            regime = "BEAR"
        else:
            regime = "SIDEWAYS"
            
        print(f"Market Regime: {regime}  (Nifty={last:.0f}, MA200={ma200:.0f})")
    else:
        regime = "SIDEWAYS"
        print("Failed to fetch Nifty50. Defaulting Market Regime: SIDEWAYS")

    print("Building LangGraph MMCI pipeline...")
    graph = build_graph()
    
    counts = {"BUY": 0, "HOLD": 0, "SELL": 0, "DISSENT": 0}
    
    print("\n" + "="*80)
    print(f"{BOLD}RUNNING SEQUENTIAL ANALYSIS{RESET}")
    print("="*80 + "\n")

    for idx, symbol in enumerate(symbols):
        symbol = symbol.upper()
        
        # Build the context
        ctx = await builder.build(symbol, symbol, "Unknown", regime)
        
        state = {
            "symbol": symbol,
            "run_id": str(uuid.uuid4()),
            "market_regime": regime,
            "stock_context": ctx,
            "model_signals": [],
            "errors": []
        }
        
        # Execute the graph
        result = await graph.ainvoke(state)
        sig = result["final_signal"]
        
        # Parse final outputs
        direction = sig.get("direction", "HOLD")
        s_score = sig.get("consensus_score", 0.0)
        d_score = sig.get("dissent_score", 0.0)
        alloc = sig.get("suggested_alloc", 0.0) * 100
        risk = sig.get("risk_level", 3)
        dissent_flag = sig.get("dissent_flag", False)
        
        # Format the line representation
        d_icon = f"{YELLOW}⚠{RESET}" if dissent_flag else " "
        
        if direction == "BUY":
            color = GREEN
            counts["BUY"] += 1
        elif direction == "SELL":
            color = RED
            counts["SELL"] += 1
        else:
            color = YELLOW
            counts["HOLD"] += 1
            if dissent_flag:
                counts["DISSENT"] += 1
                
        alloc_str = f"Alloc={alloc:02.0f}%"
        s_str = f"S={s_score:+.3f}"
        d_str = f"D={d_score:.3f}"
        
        out_line = f"[{color}{BOLD}{direction:5}{RESET}] {symbol:10} {s_str:8}  {d_str:8}  {alloc_str:10}  Risk={risk}  [{regime}] {d_icon}"
        print(out_line)
        
        # Sleep to respect Screener/News API rate limits
        if idx < len(symbols) - 1:
            await asyncio.sleep(5)
            
    print("\n" + "="*80)
    print(f"{BOLD}SUMMARY: BUY: {counts['BUY']} | HOLD: {counts['HOLD']} | SELL: {counts['SELL']} | DISSENT: {counts['DISSENT']}{RESET}")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pantheon MMCI CLI Runner")
    parser.add_argument("--symbols", nargs="+", default=None, help="List of stock symbols to evaluate")
    args = parser.parse_args()
    
    # Mute loud 3rd-party loggers if desired
    logger.disable("urllib3")
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    
    try:
        asyncio.run(main(args.symbols))
    except KeyboardInterrupt:
        print("\nAnalysis aborted by user.")
