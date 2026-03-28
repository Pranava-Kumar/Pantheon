"""
Pydantic response schemas for the Pantheon REST API.
These are read-only response models — the database writes
happen exclusively through the MMCI pipeline, never through the API.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SignalResponse(BaseModel):
    run_id: str
    symbol: str
    timestamp: datetime
    direction: str
    consensus_score: float
    dissent_score: float
    dissent_flag: bool
    market_regime: str
    suggested_alloc: float
    risk_level: int
    models_used: int
    model_signals: dict
    reasoning: str
    outcome: Optional[str] = None
    entry_price: Optional[float] = None

    model_config = {"from_attributes": True}


class TradeResponse(BaseModel):
    id: str
    signal_run_id: str
    symbol: str
    direction: str
    entry_price: float
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    pnl_pct: Optional[float] = None
    regime_at_entry: str
    is_open: bool

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    total_signals: int
    total_trades: int
    redis: Optional[str] = "disconnected"


class GateResponse(BaseModel):
    passed: int
    total: int
    ready: bool
    gate: dict
    metrics: dict


class WatchlistItem(BaseModel):
    symbol: str
    company: str
    sector: str


class AnalysisTriggerResponse(BaseModel):
    status: str
    message: str
    symbols: list[str]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(BaseModel):
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}

