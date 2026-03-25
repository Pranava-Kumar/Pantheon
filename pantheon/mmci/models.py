from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ModelID(str, Enum):
    GEMINI_PRO = "gemini_pro"
    GEMINI_FLASH = "gemini_flash"
    GROQ_QWEN = "groq_qwen"
    GROQ_LLAMA = "groq_llama"
    GROQ_GPT = "groq_gpt"

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"

class SentimentIndicator(BaseModel):
    score: float = 0.0  # -1.0 to 1.0
    label: str = "NEUTRAL" # BULLISH, BEARISH, NEUTRAL
    news_count: int = 0
    confidence: float = 0.0

class TechnicalIndicators(BaseModel):
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    atr_14: Optional[float] = None
    volume_ratio: Optional[float] = None

class FundamentalData(BaseModel):
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    promoter_pct: Optional[float] = None
    fii_pct: Optional[float] = None

class NewsItem(BaseModel):
    title: str
    source: str = ""
    published_at: str = ""
    summary: str = ""
    url: str = ""

class ModelSignal(BaseModel):
    model_id: str
    direction: str
    confidence: float
    timeframe: str
    reasoning: str = ""
    price_target: Optional[float] = None
    failed: bool = False
    failure_reason: str = ""
    latency_ms: int = 0

    def signed_confidence(self) -> float:
        d = {"BUY": 1, "SELL": -1, "HOLD": 0}.get(self.direction, 0)
        return d * self.confidence

class MCISignal(BaseModel):
    run_id: str
    symbol: str
    direction: str
    consensus_score: float
    sentiment_score: float = 0.0
    dissent_score: float
    dissent_flag: bool
    market_regime: str
    timeframe: str
    suggested_alloc: float
    risk_level: int
    models_used: int
    model_signals: list[dict]
    reasoning: str
    timestamp: str
    price_target: Optional[float] = None

    @property
    def is_actionable(self) -> bool:
        return self.direction != "HOLD" and not self.dissent_flag
