import asyncio
import uuid
from datetime import datetime
from loguru import logger

from pantheon.agents.graph import build_graph
from pantheon.data.upstox_client import UpstoxClient
from pantheon.data.nse_client import NSEClient
from pantheon.data.screener_client import ScreenerClient
from pantheon.data.news_client import NewsClient
from pantheon.data.context_builder import ContextBuilder
from pantheon.db.session import SessionLocal, init_db
from pantheon.db.models import SignalRecord, PaperTrade
from pantheon.config.settings import settings
from pantheon.config import load_watchlist
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN if hasattr(settings, "SENTRY_DSN") else "",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)



async def detect_regime(upstox: UpstoxClient) -> str:
    try:
        df = upstox.get_nifty50_history(days=250)
        ma200 = df["close"].tail(200).mean()
        last  = df["close"].iloc[-1]
        
        if last > ma200 * settings.BULL_MA200_MULTIPLIER:  
            return "BULL"
        if last < ma200 * settings.BEAR_MA200_MULTIPLIER:  
            return "BEAR"
        
        return "SIDEWAYS"
    except Exception as e:
        logger.warning(f"Regime detection failed: {e}, defaulting to SIDEWAYS")
        return "SIDEWAYS"

async def save_signal(db, signal: dict, entry_price: float) -> None:
    record = SignalRecord(
        run_id          = signal["run_id"],
        symbol          = signal["symbol"],
        direction       = signal["direction"],
        consensus_score = signal["consensus_score"],
        dissent_score   = signal["dissent_score"],
        dissent_flag    = signal["dissent_flag"],
        market_regime   = signal["market_regime"],
        suggested_alloc = signal["suggested_alloc"],
        risk_level      = signal["risk_level"],
        models_used     = signal["models_used"],
        model_signals   = signal["model_signals"],
        reasoning       = signal["reasoning"],
        entry_price     = entry_price,
    )
    db.add(record)
    
    if signal["direction"] != "HOLD" and not signal["dissent_flag"]:
        trade = PaperTrade(
            signal_run_id   = signal["run_id"],
            symbol          = signal["symbol"],
            direction       = signal["direction"],
            entry_price     = entry_price,
            regime_at_entry = signal["market_regime"],
        )
        db.add(trade)
    db.commit()

async def run_daily_analysis(symbols: list[str] | None = None) -> list[dict]:
    init_db()
    logger.info("Starting daily MMCI analysis")

    upstox   = UpstoxClient(access_token="dev_token")
    nse      = NSEClient()
    screener = ScreenerClient(settings.SCREENER_EMAIL, settings.SCREENER_PASSWORD)
    news     = NewsClient()
    builder  = ContextBuilder(upstox, nse, screener, news)
    graph    = build_graph()

    regime = await detect_regime(upstox)
    logger.info(f"Market regime: {regime}")

    watchlist = [w for w in load_watchlist()
                 if symbols is None or w["symbol"] in symbols]

    results = []
    db = SessionLocal()
    try:
        for stock in watchlist:
            sym = stock["symbol"]
            logger.info(f"Analyzing {sym}...")
            try:
                ctx = await builder.build(
                    sym, stock["company"], stock["sector"], regime)
                state = {
                    "symbol": sym,
                    "run_id": str(uuid.uuid4()),
                    "market_regime": regime,
                    "stock_context": ctx,
                    "model_signals": [],
                    "errors": []
                }
                
                result = await graph.ainvoke(state)
                signal = result["final_signal"]
                entry_price = ctx.get("current_price") or 0.0
                
                await save_signal(db, signal, entry_price)
                results.append(signal)
                
                logger.info(f"{sym}: {signal['direction']} S={signal['consensus_score']:.3f}")
            except Exception as e:
                logger.error(f"{sym} analysis failed: {e}")
                
            # 15s delay to stay under Google free tier 15 RPM limit (2 reqs/stock = 4 reqs/min max)
            await asyncio.sleep(15)
    finally:
        db.close()

    logger.info(f"Analysis complete. {len(results)} signals stored.")
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Ensure project root is on sys.path for CI environments
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    asyncio.run(run_daily_analysis())
