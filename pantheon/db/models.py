"""
Database ORM models using SQLModel.
All three tables: SignalRecord, PaperTrade, TokenRecord.
"""

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON
from typing import Optional
from datetime import datetime
import uuid


class SignalRecord(SQLModel, table=True):
    __tablename__ = "signals"

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    symbol: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    direction: str
    consensus_score: float
    dissent_score: float
    dissent_flag: bool = Field(default=False)
    market_regime: str
    suggested_alloc: float
    risk_level: int
    models_used: int

    model_signals: dict = Field(default_factory=dict, sa_column=Column(JSON))
    reasoning: str

    outcome: Optional[str] = Field(default=None)
    outcome_date: Optional[datetime] = Field(default=None)
    entry_price: Optional[float] = Field(default=None)


class PaperTrade(SQLModel, table=True):
    __tablename__ = "paper_trades"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    signal_run_id: str
    symbol: str
    direction: str
    entry_price: float
    entry_date: datetime = Field(default_factory=datetime.utcnow)

    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    pnl_pct: Optional[float] = None

    regime_at_entry: str
    is_open: bool = Field(default=True)


class TokenRecord(SQLModel, table=True):
    __tablename__ = "tokens"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider: str = Field(index=True)
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column(JSON))


class ModelWeight(SQLModel, table=True):
    """Persistent model weight storage — replaces local weights.json for CI compatibility."""
    __tablename__ = "model_weights"

    model_id: str = Field(primary_key=True)   # e.g. "gemini_pro", "groq_qwen"
    weight: float = Field(default=0.20)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

