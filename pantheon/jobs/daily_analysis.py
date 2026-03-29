import asyncio
import uuid
from datetime import datetime, timezone
from loguru import logger

from pantheon.agents.graph import build_graph
from pantheon.data.upstox_client import UpstoxClient
from pantheon.data.nse_client import NSEClient
from pantheon.data.screener_client import ScreenerClient
from pantheon.data.news_client import NewsClient
from pantheon.data.nse_sector_client import NSESectorClient
from pantheon.data.context_builder import ContextBuilder
from pantheon.data.market_regime import detect_market_regime
from pantheon.db.session import SessionLocal, init_db
from pantheon.db.models import SignalRecord, PaperTrade, TokenRecord
from pantheon.config.settings import settings
from pantheon.config import load_watchlist
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN if hasattr(settings, "SENTRY_DSN") else "",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


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

    # Load Upstox token from database
    db = SessionLocal()
    try:
        from pantheon.db.models import TokenRecord
        token_record = db.query(TokenRecord).filter_by(is_active=True).first()
        if not token_record:
            raise RuntimeError("No active Upstox token found. Please authenticate first.")
        upstox_token = token_record.access_token
    finally:
        db.close()

    upstox   = UpstoxClient(access_token=upstox_token)
    nse      = NSEClient()
    screener = ScreenerClient(settings.SCREENER_EMAIL, settings.SCREENER_PASSWORD)
    news     = NewsClient()
    sector   = NSESectorClient()
    builder  = ContextBuilder(upstox, nse, screener, news, sector)
    graph    = build_graph()

    regime = await detect_market_regime(upstox)
    logger.info(f"Market regime: {regime}")

    watchlist = [w for w in load_watchlist()
                 if symbols is None or w["symbol"] in symbols]

    results = []

    # Use semaphore to control concurrency (3 stocks at a time to balance API limits)
    semaphore = asyncio.Semaphore(3)

    async def analyze_stock(stock: dict) -> dict | None:
        """
        Analyze a single stock with rate limiting.
        Creates its own DB session for thread safety.
        """
        sym = stock["symbol"]
        # Acquire semaphore FIRST to limit concurrent DB connections
        async with semaphore:
            db = SessionLocal()  # New session per task for thread safety
            try:
                logger.info(f"Analyzing {sym}...")
                # Small delay BEFORE API call to space out requests
                await asyncio.sleep(2)
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

                    logger.info(f"{sym}: {signal['direction']} S={signal['consensus_score']:.3f}")
                    return signal
                except Exception as e:
                    logger.error(f"{sym} analysis failed: {e}")
                    return None
            finally:
                db.close()

    try:
        # Process stocks in batches with controlled concurrency
        tasks = [analyze_stock(stock) for stock in watchlist]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log individual exceptions before filtering
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Stock {watchlist[i]['symbol']} analysis failed with exception: {type(result).__name__}: {result}")

        # Filter out None results and exceptions
        results = [r for r in batch_results if r is not None and not isinstance(r, Exception)]

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")

    logger.info(f"Analysis complete. {len(results)} signals stored.")
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Ensure project root is on sys.path for CI environments
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    asyncio.run(run_daily_analysis())
