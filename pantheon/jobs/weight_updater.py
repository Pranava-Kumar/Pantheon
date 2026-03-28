import sys
from pathlib import Path
import uuid

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import datetime, timedelta, date, timezone
from loguru import logger
from sqlmodel import select

from pantheon.db.session import SessionLocal
from pantheon.db.models import SignalRecord, PaperTrade
from pantheon.data.upstox_client import UpstoxClient
from pantheon.data.weights_store import load_weights, save_weights
from pantheon.mmci.weights import WeightManager
from pantheon.config.settings import settings
from pantheon.db.token_store import get_active_upstox_token
from pantheon.db.redis_client import get_redis

OUTCOME_THRESHOLD_PCT = 2.0  # 2% move required to call BUY or SELL correct


class BatchCircuitBreaker:
    """
    Circuit breaker for batch price fetching to prevent repeated API failures.
    
    Uses asyncio.Lock for thread-safe state modifications.
    """
    
    def __init__(self):
        self.failure_count = 0
        self.failure_threshold = 3  # Skip batch after 3 consecutive failures
        self.cooldown_seconds = 300  # 5 minute cooldown after threshold reached
        self.last_failure_time: datetime | None = None
        self._lock = asyncio.Lock()
    
    async def is_open(self) -> bool:
        """Check if circuit breaker is open (should skip batch)."""
        async with self._lock:
            if self.last_failure_time is None:
                return False
            elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
            return elapsed < self.cooldown_seconds
    
    async def record_success(self):
        """Record successful batch fetch, reset failure count."""
        async with self._lock:
            self.failure_count = 0
    
    async def record_failure(self):
        """Record failed batch fetch, increment failure count."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now(timezone.utc)
            return self.failure_count


# Global circuit breaker instance for batch price fetching
batch_circuit_breaker = BatchCircuitBreaker()

def get_trading_days_ago(n: int) -> date:
    current = date.today()
    days_counted = 0
    while days_counted < n:
        current -= timedelta(days=1)
        if current.weekday() < 5:  # 0=Monday, 4=Friday
            days_counted += 1
    return current

def determine_actual_outcome(signal_direction: str, entry_price: float, current_price: float) -> str:
    """
    Determine if a signal's prediction was correct based on price movement.
    
    For BUY signals: correct if price increased >= threshold
    For SELL signals: correct if price decreased >= threshold
    For HOLD signals: correct if price stayed within threshold
    
    Args:
        signal_direction: The predicted direction (BUY/SELL/HOLD)
        entry_price: The entry price when signal was generated
        current_price: The current/outcome price
        
    Returns:
        "BUY" if price moved up >= threshold
        "SELL" if price moved down >= threshold  
        "HOLD" if price stayed within threshold
    """
    if not entry_price:
        return "HOLD"
    pct_change = (current_price - entry_price) / entry_price * 100.0
    
    # Determine outcome based on signal direction
    if signal_direction == "BUY":
        if pct_change >= OUTCOME_THRESHOLD_PCT:
            return "BUY"  # Correct: price went up
        elif pct_change <= -OUTCOME_THRESHOLD_PCT:
            return "SELL"  # Incorrect: price went down
    elif signal_direction == "SELL":
        if pct_change <= -OUTCOME_THRESHOLD_PCT:
            return "SELL"  # Correct: price went down
        elif pct_change >= OUTCOME_THRESHOLD_PCT:
            return "BUY"  # Incorrect: price went up
    
    return "HOLD"  # Price stayed within threshold

async def _process_update_for_date(target_date: date) -> dict:
    logger.info(f"Running T+5 update for signals from {target_date}")
    db = SessionLocal()
    redis = get_redis()
    lock_key = "weight_update_lock"
    lock_timeout = 300  # 5 minutes
    lock_token = str(uuid.uuid4())  # Unique token to ensure only owner can release
    lock_acquired = False

    # Acquire distributed lock using Redis to prevent concurrent weight updates
    if redis:
        try:
            # Try to acquire lock with unique token (non-blocking)
            lock_acquired = await redis.set(lock_key, lock_token, nx=True, ex=lock_timeout)
            if not lock_acquired:
                logger.info("Weight update already running, skipping")
                db.close()  # Close DB before early return
                await redis.close()
                redis = None  # Prevent double-close in finally block
                return {}
        except Exception as e:
            logger.error(f"Redis lock acquisition failed, skipping weight update: {e}")
            # Alert operations team for monitoring (Sentry, PagerDuty, etc.)
            try:
                import sentry_sdk
                sentry_sdk.capture_message(f"Weight update skipped: Redis lock failed - {e}", level="error")
            except Exception:
                pass  # Sentry may not be configured
            db.close()  # Close DB before early return
            await redis.close()  # Close Redis connection on error path
            redis = None  # Prevent double-close in finally block
            return {}  # Fail closed - skip update if Redis unavailable
    else:
        logger.warning("Redis not available, proceeding without distributed lock")

    try:
        # Time boundaries for robust date filtering across SQL dialects
        start_t = datetime.combine(target_date, datetime.min.time())
        end_t = start_t + timedelta(days=1)

        stmt = select(SignalRecord).where(
            SignalRecord.outcome == None,
            SignalRecord.timestamp >= start_t,
            SignalRecord.timestamp < end_t
        )
        records = db.exec(stmt).all()

        if not records:
            logger.info("No signals to evaluate for this date")
            return {}

        # Load Upstox token from database (FIX: was hardcoded "dev_token")
        upstox_token = get_active_upstox_token()
        upstox = UpstoxClient(access_token=upstox_token)
        weights = load_weights()
        wm = WeightManager(weights)

        # FIX: Batch price requests to avoid N+1 API calls
        # Collect all instrument keys first
        symbol_to_record = {}
        instrument_keys = []
        for record in records:
            try:
                instrument_key = upstox.get_instrument_key(record.symbol)
                if instrument_key:
                    symbol_to_record[record.symbol] = (record, instrument_key)
                    instrument_keys.append(instrument_key)
            except Exception as e:
                logger.warning(f"Failed to get instrument key for {record.symbol}: {e}")

        # Fetch all prices in a single batch request with circuit breaker
        batch_prices = {}
        if instrument_keys:
            # Check circuit breaker cooldown
            if await batch_circuit_breaker.is_open():
                logger.info(f"Batch price fetch in cooldown, using individual requests")
            else:
                try:
                    batch_prices = upstox.get_batch_prices(instrument_keys)
                    # Reset failure count on success
                    await batch_circuit_breaker.record_success()
                except Exception as e:
                    failure_count = await batch_circuit_breaker.record_failure()
                    logger.error(f"Batch price fetch failed ({failure_count}/{batch_circuit_breaker.failure_threshold}), falling back to individual requests: {e}")
                    if failure_count >= batch_circuit_breaker.failure_threshold:
                        logger.warning(f"Batch circuit breaker triggered, will retry after {batch_circuit_breaker.cooldown_seconds}s")
                    # batch_prices remains empty, will trigger individual fetches below

        for record in records:
            try:
                if record.symbol not in symbol_to_record:
                    continue
                _, instrument_key = symbol_to_record[record.symbol]

                # Use batch price if available, otherwise fall back to individual request
                current_price = batch_prices.get(instrument_key)
                if current_price is None:  # Explicit None check (0.0 is valid price)
                    try:
                        current_price = upstox.get_current_price(instrument_key, record.symbol)
                    except Exception as e:
                        logger.warning(f"Individual price fetch failed for {record.symbol}: {e}")
                        continue  # Skip this record

                if not current_price or not record.entry_price:
                    continue

                # FIX: Determine outcome based on signal direction
                actual = determine_actual_outcome(record.direction, record.entry_price, current_price)
                pct = (current_price - record.entry_price) / record.entry_price * 100.0

                logger.info(f"{record.symbol}: signal={record.direction} actual={actual} pct={pct:+.2f}%")

                # Update signal record
                record.outcome = actual
                record.outcome_date = datetime.now(timezone.utc)

                # Update paper trade if exists
                trade = db.exec(
                    select(PaperTrade).where(
                        PaperTrade.signal_run_id == record.run_id,
                        PaperTrade.is_open == True
                    )
                ).first()

                if trade:
                    trade.exit_price = current_price
                    trade.exit_date = datetime.now(timezone.utc)
                    # FIX: Invert P&L for SELL signals
                    trade.pnl_pct = -pct if trade.direction == "SELL" else pct
                    trade.is_open = False

                # Feed signal to weight manager
                signals = record.model_signals  # list of dicts
                wm.update(signals, actual)

            except Exception as e:
                logger.error(f"Weight update failed for {record.symbol}: {e}")

        db.commit()
        new_weights = wm.get_weights()
        save_weights(new_weights)
        logger.info(f"Weights updated: {new_weights}")
        return new_weights

    finally:
        db.close()
        # Release lock atomically using Lua script (prevents race condition)
        if redis and lock_acquired:
            try:
                # Atomic lock release: only delete if we still own the lock
                unlock_script = """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                else
                    return 0
                end
                """
                result = await redis.eval(unlock_script, 1, lock_key, lock_token)
                if result:
                    logger.debug("Weight update lock released successfully")
                else:
                    logger.warning("Weight update lock was already released or stolen")
            except Exception as e:
                logger.warning(f"Failed to release lock: {e}")
        # Close Redis connection explicitly
        if redis:
            try:
                await redis.close()
            except Exception as e:
                logger.warning(f"Failed to close Redis connection: {e}")

async def run_weight_update() -> dict:
    target_date = get_trading_days_ago(5)
    return await _process_update_for_date(target_date)

async def run_manual_update_for_date(target_date_str: str) -> dict:
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    return await _process_update_for_date(target_date)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD to manually run for past dates")
    args = parser.parse_args()
    
    if args.date:
        asyncio.run(run_manual_update_for_date(args.date))
    else:
        asyncio.run(run_weight_update())
