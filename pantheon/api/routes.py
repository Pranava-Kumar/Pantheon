"""
API route definitions for Project Pantheon.
All endpoints are read-only except /trigger which kicks off analysis.
"""

from datetime import datetime, date, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, func, col

from pantheon.db.session import get_db, init_db
from pantheon.db.models import SignalRecord, PaperTrade, User
from pantheon.config import load_watchlist
from pantheon.api.schemas import (
    SignalResponse, TradeResponse, HealthResponse,
    GateResponse, WatchlistItem, AnalysisTriggerResponse,
    Token, UserResponse
)
from pantheon.auth.jwt_handler import create_access_token
from pantheon.auth.utils import verify_password
from pantheon.auth.dependencies import get_current_active_user
from pantheon.api.rate_limiter import RateLimiter

# Global rate limiter for general endpoints
global_rate_limiter = RateLimiter(requests_limit=60, window_seconds=60)
# Stricter rate limiter for authentication endpoints (prevent brute-force)
auth_rate_limiter = RateLimiter(requests_limit=5, window_seconds=60)

router = APIRouter(
    prefix="/api/v1",
    tags=["Pantheon API"],
    dependencies=[Depends(global_rate_limiter)]
)


# ──────────────────────────────────────────────
# AUTHENTICATION
# ──────────────────────────────────────────────
@router.post("/token", response_model=Token, dependencies=[Depends(auth_rate_limiter)])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


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
        timestamp=datetime.now(timezone.utc),
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
    from pantheon.jobs.paper_trading_tracker import check_exit_gate
    result = check_exit_gate()
    return GateResponse(**result)


# ──────────────────────────────────────────────
# TRIGGER (for cron-job.org or manual use)
# ──────────────────────────────────────────────
async def _run_analysis_background(symbols: list[str] | None):
    from pantheon.jobs.daily_analysis import run_daily_analysis
    await run_daily_analysis(symbols)


@router.post("/trigger", response_model=AnalysisTriggerResponse)
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    symbols: list[str] | None = Query(None, description="Symbols to analyze (None = full watchlist)"),
):
    target_symbols = symbols or [w["symbol"] for w in load_watchlist()]

    background_tasks.add_task(_run_analysis_background, symbols)
    return AnalysisTriggerResponse(
        status="accepted",
        message="MMCI analysis queued in background",
        symbols=target_symbols,
    )
