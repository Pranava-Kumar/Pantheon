import sys
from pathlib import Path

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import datetime, timedelta, date
from loguru import logger
from sqlalchemy import func

from db.session import SessionLocal
from db.models import SignalRecord, PaperTrade
from data.upstox_client import UpstoxClient
from data.weights_store import load_weights, save_weights
from mmci.weights import WeightManager
from config.settings import settings

OUTCOME_THRESHOLD_PCT = 2.0  # 2% move required to call BUY or SELL correct

def get_trading_days_ago(n: int) -> date:
    current = date.today()
    days_counted = 0
    while days_counted < n:
        current -= timedelta(days=1)
        if current.weekday() < 5:  # 0=Monday, 4=Friday
            days_counted += 1
    return current

def determine_actual_outcome(entry_price: float, current_price: float) -> str:
    if not entry_price:
        return "HOLD"
    pct_change = (current_price - entry_price) / entry_price * 100.0
    if pct_change >= OUTCOME_THRESHOLD_PCT:
        return "BUY"
    if pct_change <= -OUTCOME_THRESHOLD_PCT:
        return "SELL"
    return "HOLD"

async def _process_update_for_date(target_date: date) -> dict:
    logger.info(f"Running T+5 update for signals from {target_date}")
    db = SessionLocal()
    
    try:
        # Time boundaries for robust date filtering across SQL dialects
        start_t = datetime.combine(target_date, datetime.min.time())
        end_t = start_t + timedelta(days=1)
        
        records = db.query(SignalRecord).filter(
            SignalRecord.outcome == None,
            SignalRecord.timestamp >= start_t,
            SignalRecord.timestamp < end_t
        ).all()

        if not records:
            logger.info("No signals to evaluate for this date")
            return {}

        upstox = UpstoxClient(access_token="dev_token")
        weights = load_weights()
        wm = WeightManager(weights)

        for record in records:
            try:
                instrument_key = upstox.get_instrument_key(record.symbol)
                current_price = upstox.get_current_price(instrument_key, record.symbol)
                
                if not current_price or not record.entry_price:
                    continue

                actual = determine_actual_outcome(record.entry_price, current_price)
                pct = (current_price - record.entry_price) / record.entry_price * 100.0

                logger.info(f"{record.symbol}: signal={record.direction} actual={actual} pct={pct:+.2f}%")

                # Update signal record
                record.outcome = actual
                record.outcome_date = datetime.utcnow()

                # Update paper trade if exists
                trade = db.query(PaperTrade).filter_by(
                    signal_run_id=record.run_id, is_open=True
                ).first()
                
                if trade:
                    trade.exit_price = current_price
                    trade.exit_date = datetime.utcnow()
                    trade.pnl_pct = pct
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
