"""
API route definitions for Project Pantheon.
All endpoints are read-only except /trigger which kicks off analysis.
"""

import asyncio
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlmodel import Session, select, func, col

from db.session import get_db, init_db
from db.models import SignalRecord, PaperTrade
from config import load_watchlist
from api.schemas import (
    SignalResponse, TradeResponse, HealthResponse,
    GateResponse, WatchlistItem, AnalysisTriggerResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Pantheon API"])


# ──────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    total_signals = db.exec(select(func.count(SignalRecord.run_id))).one()
    total_trades = db.exec(select(func.count(PaperTrade.id))).one()
    return HealthResponse(
        status="ok",
        database="connected",
        timestamp=datetime.utcnow(),
        total_signals=total_signals,
        total_trades=total_trades,
    )


# ──────────────────────────────────────────────
# SIGNALS
# ──────────────────────────────────────────────
@router.get("/signals", response_model=list[SignalResponse])
def get_signals(
    symbol: str | None = Query(None, description="Filter by stock symbol"),
    direction: str | None = Query(None, description="Filter by BUY/SELL/HOLD"),
    regime: str | None = Query(None, description="Filter by market regime"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(SignalRecord).order_by(col(SignalRecord.timestamp).desc())
    if symbol:
        stmt = stmt.where(SignalRecord.symbol == symbol.upper())
    if direction:
        stmt = stmt.where(SignalRecord.direction == direction.upper())
    if regime:
        stmt = stmt.where(SignalRecord.market_regime == regime.upper())
    stmt = stmt.limit(limit)
    return db.exec(stmt).all()


@router.get("/signals/today", response_model=list[SignalResponse])
def get_todays_signals(db: Session = Depends(get_db)):
    today = date.today()
    stmt = (
        select(SignalRecord)
        .where(func.date(SignalRecord.timestamp) == today)
        .order_by(col(SignalRecord.consensus_score).desc())
    )
    return db.exec(stmt).all()


@router.get("/signals/{symbol}", response_model=list[SignalResponse])
def get_signal_history(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = (
        select(SignalRecord)
        .where(SignalRecord.symbol == symbol.upper())
        .order_by(col(SignalRecord.timestamp).desc())
        .limit(limit)
    )
    return db.exec(stmt).all()


# ──────────────────────────────────────────────
# PAPER TRADES
# ──────────────────────────────────────────────
@router.get("/trades", response_model=list[TradeResponse])
def get_trades(
    open_only: bool = Query(False, description="Only show open trades"),
    symbol: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(PaperTrade).order_by(col(PaperTrade.entry_date).desc())
    if open_only:
        stmt = stmt.where(PaperTrade.is_open == True)
    if symbol:
        stmt = stmt.where(PaperTrade.symbol == symbol.upper())
    stmt = stmt.limit(limit)
    return db.exec(stmt).all()


# ──────────────────────────────────────────────
# WATCHLIST
# ──────────────────────────────────────────────
@router.get("/watchlist", response_model=list[WatchlistItem])
def get_watchlist():
    return load_watchlist()


# ──────────────────────────────────────────────
# EXIT GATE
# ──────────────────────────────────────────────
@router.get("/gate", response_model=GateResponse)
def get_exit_gate():
    from jobs.paper_trading_tracker import check_exit_gate
    result = check_exit_gate()
    return GateResponse(**result)


# ──────────────────────────────────────────────
# TRIGGER (for cron-job.org or manual use)
# ──────────────────────────────────────────────
async def _run_analysis_background(symbols: list[str] | None):
    from jobs.daily_analysis import run_daily_analysis
    await run_daily_analysis(symbols)


@router.post("/trigger", response_model=AnalysisTriggerResponse)
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    symbols: list[str] | None = Query(None, description="Symbols to analyze (None = full watchlist)"),
):
    target_symbols = symbols or [w["symbol"] for w in load_watchlist()]
    background_tasks.add_task(_run_analysis_background, symbols)
    return AnalysisTriggerResponse(
        status="accepted",
        message="MMCI analysis queued in background",
        symbols=target_symbols,
    )
