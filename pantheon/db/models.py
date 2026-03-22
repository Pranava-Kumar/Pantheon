from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class SignalRecord(Base):
    __tablename__ = "signals"
    run_id          = Column(String(36), primary_key=True,
                             default=lambda: str(uuid.uuid4()))
    symbol          = Column(String(20), nullable=False, index=True)
    timestamp       = Column(DateTime, nullable=False, default=datetime.utcnow)
    direction       = Column(String(4), nullable=False)
    consensus_score = Column(Float, nullable=False)
    dissent_score   = Column(Float, nullable=False)
    dissent_flag    = Column(Boolean, nullable=False, default=False)
    market_regime   = Column(String(10), nullable=False)
    suggested_alloc = Column(Float, nullable=False)
    risk_level      = Column(Integer, nullable=False)
    models_used     = Column(Integer, nullable=False)
    model_signals   = Column(JSON, nullable=False)
    reasoning       = Column(Text, nullable=False)
    outcome         = Column(String(4), nullable=True)
    outcome_date    = Column(DateTime, nullable=True)
    entry_price     = Column(Float, nullable=True)

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id              = Column(String(36), primary_key=True,
                             default=lambda: str(uuid.uuid4()))
    signal_run_id   = Column(String(36), nullable=False)
    symbol          = Column(String(20), nullable=False)
    direction       = Column(String(4), nullable=False)
    entry_price     = Column(Float, nullable=False)
    entry_date      = Column(DateTime, nullable=False, default=datetime.utcnow)
    exit_price      = Column(Float, nullable=True)
    exit_date       = Column(DateTime, nullable=True)
    pnl_pct         = Column(Float, nullable=True)
    regime_at_entry = Column(String(10), nullable=False)
    is_open         = Column(Boolean, nullable=False, default=True)
