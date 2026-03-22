# System Design Document
## Project Pantheon — Multi-Model Consensus Intelligence System

**Document Version:** 1.0  
**Date:** March 21, 2026  
**Status:** Draft — Pending Developer Review  
**SDLC Phase:** Phase 2 — System Design  
**Prerequisite:** SRS v1.0 (approved)  
**SRS Traceability:** All design decisions traced to FR-01 through C-09

---

## Part 1 — High-Level Design (HLD)

### 1.1 System Architecture Overview

Pantheon is composed of six distinct subsystems. Each subsystem has a single clear responsibility and communicates with others through defined interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                        PANTHEON SYSTEM                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  DATA LAYER  │    │  MMCI ENGINE │    │  PERSISTENCE     │  │
│  │              │───▶│              │───▶│  LAYER           │  │
│  │ Upstox API   │    │ LangGraph    │    │                  │  │
│  │ NSE APIs     │    │ Graph        │    │ PostgreSQL       │  │
│  │ Screener.in  │    │              │    │ LangSmith        │  │
│  │ RSS News     │    │ 5 Model      │    │ LangGraph Store  │  │
│  │ FII/DII      │    │ Nodes        │    │                  │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘  │
│                             │                                    │
│  ┌──────────────┐           │            ┌──────────────────┐  │
│  │  AUTH LAYER  │           ▼            │  SCHEDULER       │  │
│  │              │    ┌──────────────┐    │                  │  │
│  │ OAuth 2.0    │    │  SIGNAL OUT  │    │ Daily Analysis   │  │
│  │ Token Store  │    │              │    │ News Poller      │  │
│  │ Notifier URL │    │ MCISignal    │    │ T+5 Weight Job   │  │
│  └──────────────┘    │ Dashboard    │    │ Token Refresh    │  │
│                       └──────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 End-to-End Data Flow

```
DAILY ANALYSIS RUN (triggered at 5:00 PM IST)
│
├─[1] Auth Check
│    └── UpstoxAuthManager.get_valid_token()
│        If token expired → alert developer → abort
│
├─[2] Market Regime Detection
│    └── Fetch Nifty 50 last 200 days via Upstox
│        Compute MA_200 → classify BULL/BEAR/SIDEWAYS
│
├─[3] For each symbol in watchlist [batches of 10]:
│    │
│    ├─[3a] StockContext Assembly (parallel sub-tasks)
│    │    ├── Upstox: 60-day OHLCV → compute 8 indicators (pandas-ta)
│    │    ├── NSE Bhav Copy: delivery %, short selling %
│    │    ├── NSE API: bulk deals (7d), insider trades (30d), FII/DII flows
│    │    ├── Screener.in: fundamentals (cache-first, 7-day TTL)
│    │    ├── NewsDB: last 48h articles matching symbol
│    │    ├── Finnhub: days until next earnings
│    │    └── Assemble → StockContext object
│    │
│    ├─[3b] LangGraph MMCI Pipeline
│    │    ├── data_ingestion_node → StockContext into state
│    │    ├── regime_detection_node → MarketRegime into state
│    │    ├── prompt_builder_node → 5 model-specific prompts
│    │    ├── [PARALLEL SUPERSTEP] 5 model nodes simultaneously:
│    │    │    ├── gemini_pro_node
│    │    │    ├── gemini_flash_node
│    │    │    ├── groq_qwen_node
│    │    │    ├── groq_llama_node
│    │    │    └── deepseek_node
│    │    ├── dissent_check_node (defer=True)
│    │    │    ├── IF D > 0.15 → hold_output_node → MCISignal(HOLD)
│    │    │    └── IF D ≤ 0.15 → consensus_scoring_node
│    │    ├── consensus_scoring_node → S, direction
│    │    ├── position_sizing_node → alloc, risk_level
│    │    └── output_node → MCISignal
│    │
│    └─[3c] Persistence
│         ├── Store MCISignal in PostgreSQL signals table
│         └── Log to LangSmith trace
│
├─[4] Dashboard Refresh
│    └── Streamlit reads from PostgreSQL → renders updated signals
│
└─[5] T+5 Weight Update (separate scheduled job)
     └── Runs 5 trading days after each signal
         Fetches actual price change → updates model weights
         Stores in LangGraph Long-Term Store
```

### 1.3 Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.11+ | All backend code |
| Orchestration | LangGraph | 1.0.x | MMCI graph execution |
| LLM framework | LangChain | 1.0.x | Model wrappers, tools |
| Primary model | Gemini 2.5 Pro/Flash | via API | Reasoning + web intel |
| Fast inference | Groq Qwen3 32B, Llama 3.3 70B | via API | Quant + general |
| CoT model | DeepSeek R1 | via API | Chain-of-thought |
| Data validation | Pydantic | v2.x | All data contracts |
| Database | PostgreSQL | 15+ | Signal store, news, weights |
| Checkpointing | langgraph-checkpoint-sqlite | 4.0.x (dev) | Graph state persistence |
| Checkpointing | langgraph-checkpoint-postgres | 4.0.x (prod) | Production graph state |
| Market data | Upstox Python SDK | 2.0+ | OHLCV, portfolio, orders |
| Technical analysis | pandas-ta | 0.3.14+ | 8 indicators |
| News parsing | feedparser | 6.0+ | RSS pipeline |
| Fundamental scraping | requests + bs4 | latest | Screener.in |
| Task scheduling | APScheduler | 3.10+ | Daily jobs, T+5 update |
| Dashboard | Streamlit | 1.30+ | Signal visualization |
| Observability | LangSmith | cloud | Trace all graph runs |
| Auth | OAuth 2.0 | Upstox implementation | API access |
| IDE | Antigravity IDE | — | Development |
| Vibe coding | Cline (BYOK Gemini) | — | Agentic implementation |

### 1.4 Deployment Architecture (Phase 1 — Development)

```
Your Laptop (8 GB RAM, Chennai)
├── Static IP [registered with Upstox — SEBI mandate]
├── Python 3.11 environment
├── PostgreSQL (local)
├── Pantheon application
│   ├── Daily analysis job (manual trigger or cron)
│   ├── News poller (background thread)
│   ├── Streamlit dashboard (localhost:8501)
│   └── Notifier URL handler (localhost:8000 — for Upstox token callback)
└── LangSmith (cloud — traces only, no data storage)
```

---

## Part 2 — Complete Project File Structure

Every file that will exist in the Pantheon repository. This is the authoritative directory structure.

```
pantheon/
│
├── .env                          # API keys — NEVER commit (git-ignored)
├── .env.example                  # Template showing all required env vars
├── .gitignore                    # Comprehensive Python + project ignores
├── README.md                     # Project overview
├── requirements.txt              # All Python dependencies pinned
├── pyproject.toml                # Project metadata + tool config (pytest, ruff)
│
├── config/
│   ├── __init__.py
│   ├── settings.py               # All configuration constants (thresholds, limits)
│   ├── watchlist.yaml            # 35-stock pilot watchlist with metadata
│   └── prompts/
│       ├── gemini_pro.txt        # Gemini Pro system prompt template
│       ├── gemini_flash.txt      # Gemini Flash system prompt template
│       ├── groq_qwen.txt         # Groq Qwen3 32B prompt template
│       ├── groq_llama.txt        # Groq Llama 3.3 70B prompt template
│       └── deepseek.txt          # DeepSeek R1 prompt template
│
├── pantheon/
│   ├── __init__.py
│   │
│   ├── mmci/                     # CORE ALGORITHM — never open-sourced
│   │   ├── __init__.py
│   │   ├── models.py             # All Pydantic data contracts [WRITTEN]
│   │   ├── scoring.py            # Pure math: dissent, consensus, sizing [WRITTEN]
│   │   └── weights.py            # Dynamic weight management [WRITTEN]
│   │
│   ├── agents/                   # LANGGRAPH GRAPH — never open-sourced
│   │   ├── __init__.py
│   │   ├── state.py              # PantheonState TypedDict [WRITTEN]
│   │   └── graph.py              # LangGraph graph assembly [WRITTEN]
│   │
│   ├── extractors/               # MODEL ADAPTERS — never open-sourced
│   │   ├── __init__.py
│   │   ├── base.py               # AbstractExtractor interface
│   │   ├── prompts.py            # StockContext → prompt string builders
│   │   ├── gemini_pro.py         # Gemini 2.5 Pro extractor
│   │   ├── gemini_flash.py       # Gemini 2.5 Flash extractor
│   │   ├── groq_qwen.py          # Groq Qwen3 32B extractor
│   │   ├── groq_llama.py         # Groq Llama 3.3 70B extractor
│   │   └── deepseek.py           # DeepSeek R1 extractor
│   │
│   ├── data/                     # DATA PIPELINE — can be open-sourced
│   │   ├── __init__.py
│   │   ├── upstox_client.py      # Upstox API wrapper (OHLCV, quotes)
│   │   ├── nse_client.py         # NSE internal API endpoints
│   │   ├── bhav_copy.py          # NSE Bhav Copy + delivery volume downloader
│   │   ├── screener_client.py    # Screener.in scraper (fundamentals)
│   │   ├── news_client.py        # RSS poller + storage
│   │   ├── finnhub_client.py     # Finnhub earnings calendar
│   │   ├── indicators.py         # pandas-ta technical indicator computation
│   │   ├── context_builder.py    # Assembles StockContext from all sources
│   │   └── weights_store.py      # Load/save weights from LangGraph Store
│   │
│   ├── db/                       # DATABASE — can be open-sourced
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy ORM table definitions
│   │   ├── session.py            # DB session factory (sync + async)
│   │   └── migrations/
│   │       └── env.py            # Alembic migration environment
│   │
│   ├── auth/                     # AUTH — can be open-sourced
│   │   ├── __init__.py
│   │   └── upstox_auth.py        # OAuth flow, token store, notifier handler
│   │
│   ├── jobs/                     # SCHEDULERS — can be open-sourced
│   │   ├── __init__.py
│   │   ├── daily_analysis.py     # Main daily pipeline orchestrator
│   │   ├── news_poller.py        # RSS feed background job
│   │   ├── weight_updater.py     # T+5 weight update job
│   │   └── scheduler.py          # APScheduler configuration
│   │
│   └── dashboard/                # DASHBOARD — can be open-sourced
│       ├── __init__.py
│       ├── app.py                # Main Streamlit app
│       └── components/
│           ├── signal_table.py   # Today's signals component
│           ├── weight_chart.py   # Model weight history chart
│           ├── accuracy_panel.py # Model accuracy metrics
│           └── paper_trade.py    # Paper trading tracker
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures (mock clients, sample data)
│   ├── test_mmci_core.py         # MMCI math unit tests [WRITTEN — 20+ tests]
│   ├── test_scoring.py           # Additional scoring edge cases
│   ├── test_weights.py           # Weight manager tests
│   ├── test_context_builder.py   # StockContext assembly tests (mocked APIs)
│   ├── test_extractors.py        # Extractor tests (mocked LLM calls)
│   ├── test_graph.py             # LangGraph integration test (mocked)
│   └── fixtures/
│       ├── sample_ohlcv.json     # Sample 60-day OHLCV data
│       ├── sample_fundamentals.json
│       ├── sample_news.json
│       └── sample_signal.json
│
├── scripts/
│   ├── run_analysis.py           # CLI: run MMCI for today
│   ├── run_backtest.py           # CLI: run historical backtest
│   ├── init_db.py                # DB initialization (create tables)
│   ├── generate_token.py         # Manual Upstox token generation helper
│   └── check_health.py           # System health check (all APIs reachable)
│
└── logs/                         # Rotating log files (git-ignored)
    └── .gitkeep
```

### 2.1 Open-Source Boundary

When releasing the partial open-source version:

| Directory / File | Status | Reason |
|---|---|---|
| `pantheon/mmci/` | ❌ PRIVATE | Core algorithm — the IP |
| `pantheon/agents/` | ❌ PRIVATE | Graph topology — the IP |
| `pantheon/extractors/` | ❌ PRIVATE | Prompt engineering — the IP |
| `config/prompts/` | ❌ PRIVATE | Prompt templates — the IP |
| `pantheon/data/` | ✅ Open | Data pipeline — community value |
| `pantheon/db/` | ✅ Open | Schema + migrations — community value |
| `pantheon/auth/` | ✅ Open | Auth flow — community value |
| `pantheon/jobs/` | ✅ Open | Scheduler — community value |
| `pantheon/dashboard/` | ✅ Open | Dashboard — community value |
| `tests/test_mmci_core.py` | ❌ PRIVATE | Tests reveal algorithm internals |
| Other tests | ✅ Open | Community benefit |

The research paper publishes the algorithm formula. The repository keeps the trained weights, calibrated thresholds, and prompt engineering private. That combination is the defensible moat.

---

## Part 3 — Low-Level Design (LLD)

### 3.1 Configuration Module (`config/settings.py`)

All constants that control system behaviour. Change here — not scattered in code.

```python
# config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ── LLM Providers ──────────────────────────────────────
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    DEEPSEEK_API_KEY: str
    OPENROUTER_API_KEY: str
    MISTRAL_API_KEY: str              # Failover only
    SAMBANOVA_API_KEY: str            # Failover only

    # ── Upstox ─────────────────────────────────────────────
    UPSTOX_API_KEY: str
    UPSTOX_API_SECRET: str
    UPSTOX_REDIRECT_URI: str
    UPSTOX_NOTIFIER_PORT: int = 8000

    # ── Database ────────────────────────────────────────────
    DATABASE_URL: str                 # postgresql://user:pass@localhost/pantheon
    DATABASE_URL_ASYNC: str           # postgresql+asyncpg://...

    # ── LangSmith ───────────────────────────────────────────
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "pantheon-mmci"

    # ── External APIs ────────────────────────────────────────
    FINNHUB_API_KEY: str
    SCREENER_EMAIL: str
    SCREENER_PASSWORD: str

    # ── MMCI Algorithm Parameters ────────────────────────────
    DISSENT_THRESHOLD: float = 0.15
    LEARNING_RATE: float = 0.05
    MAX_ALLOC: float = 0.20
    WEIGHT_FLOOR: float = 0.05
    WEIGHT_CEILING: float = 0.40
    MIN_MODELS_REQUIRED: int = 3
    MODEL_TIMEOUT_SECONDS: int = 20
    MODEL_RETRY_ATTEMPTS: int = 3

    # ── Regime Thresholds ────────────────────────────────────
    BULL_MA200_MULTIPLIER: float = 1.02
    BEAR_MA200_MULTIPLIER: float = 0.98

    # ── Rate Limit Budgets ───────────────────────────────────
    GEMINI_PRO_DAILY_BUDGET: int = 90     # Leave 10 RPD buffer from 100
    GEMINI_FLASH_DAILY_BUDGET: int = 200  # Leave 50 RPD buffer from 250
    BATCH_SIZE: int = 10                  # Stocks per analysis batch

    # ── Caching ──────────────────────────────────────────────
    FUNDAMENTALS_CACHE_DAYS: int = 7
    NEWS_RETENTION_HOURS: int = 72
    NODE_CACHE_TTL_HOURS: int = 4

    # ── Analysis Schedule ────────────────────────────────────
    ANALYSIS_HOUR_IST: int = 17           # 5:00 PM IST
    ANALYSIS_MINUTE_IST: int = 0
    NEWS_POLL_INTERVAL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

### 3.2 Data Layer Module Design

#### 3.2.1 `data/upstox_client.py`

```
Class: UpstoxClient
Responsibility: All Upstox REST API interactions
Depends on: auth/upstox_auth.py (for token), settings.py

Methods:
  __init__(auth_manager: UpstoxAuthManager)
    → Initializes upstox_python_sdk with auth manager's current token

  async get_historical_ohlcv(symbol: str, days: int = 60) -> PriceHistory
    → Calls /v3/historical-candle/{instrument_key}/days/1/{to_date}/{from_date}
    → Returns PriceHistory Pydantic model with dates, open, high, low, close, volume
    → Handles API errors, falls back to yfinance on 5xx
    [Satisfies: FR-02, IR-01]

  async get_nifty50_history(days: int = 250) -> list[float]
    → Fetches Nifty 50 index daily closes for last 250 days
    → Used by regime detection (FR-01)
    → Instrument key: "NSE_INDEX|Nifty 50"

  async get_market_quote(symbol: str) -> float
    → Returns LTP (last traded price) for current price snapshot
    [Used by paper trading exit price calculation]

  async get_holdings() -> list[dict]
    → Uses extended token (1-year validity)
    → Returns current holdings in Demat account

  async get_instrument_key(nse_symbol: str) -> str
    → Looks up the Upstox instrument key for a given NSE symbol
    → Uses the instruments CSV (downloaded once, cached locally)
    → Example: "WIPRO" → "NSE_EQ|INE075A01022"
```

#### 3.2.2 `data/nse_client.py`

```
Class: NSEClient
Responsibility: All NSE internal API endpoint calls
Depends on: requests.Session with cookie initialization

Methods:
  __init__()
    → Creates requests.Session, loads NSE home page to set cookies
    → Sets standard browser headers to avoid bot detection

  async get_bulk_block_deals(symbol: str, days: int = 7) -> list[BulkDealItem]
    → Calls NSE Large Deal API
    → Filters for symbol matches in last N days
    → Returns list of BulkDealItem with: date, client, deal_type, quantity, price
    [Satisfies: FR-02 — StockContext bulk_deals_7d field]

  async get_insider_trades(symbol: str, days: int = 30) -> list[InsiderTrade]
    → Calls NSE corporates-pit endpoint
    → Returns insider transactions with: person, transaction_type, shares, value
    [Satisfies: FR-02 — insider_trades_30d field]

  async get_fii_dii_flows(days: int = 7) -> FIIDIIData
    → Calls NSE fiidiiTradeReact endpoint for daily data
    → Aggregates last N days into net flow
    → Returns: fii_cash_net, dii_cash_net (₹ crores)
    [Satisfies: FR-02 — fii_cash_net_7d, dii_cash_net_7d fields]

  async get_fii_futures_positions() -> float
    → Fetches FII index futures long/short ratio from NSE reports
    → Returns long % as a float in [0, 1]
    [Satisfies: FR-02 — fii_futures_long field]

  async get_delivery_volume_pct(symbol: str) -> float
    → Reads today's NSE Delivery Bhav Copy
    → Computes deliverable_qty / total_qty for symbol
    → Returns float in [0, 1]
    [Satisfies: FR-02 — delivery_pct field]

  async get_board_meetings(symbol: str, days_ahead: int = 14) -> list[BoardMeeting]
    → Calls NSE corporate-board-meetings endpoint
    → Filters for target symbol in next N days
    → Returns meeting dates with purpose (results, dividend, etc.)
    [Satisfies: FR-02 — earnings context]

  _refresh_session() -> None
    → Re-initializes the session (NSE sessions expire after ~30 min of inactivity)
    → Called automatically on 401/403 responses
```

#### 3.2.3 `data/screener_client.py`

```
Class: ScreenerClient
Responsibility: Screener.in fundamental data with 7-day PostgreSQL cache
Depends on: db/session.py, settings.py

Methods:
  __init__(db_session)
    → Initializes requests.Session, logs in to Screener.in with credentials
    → Verifies login succeeded

  async get_fundamentals(symbol: str) -> FundamentalData
    → CHECK CACHE FIRST: SELECT from fundamentals_cache WHERE symbol=? AND fetched_at > NOW()-7days
    → If cache hit: return cached FundamentalData
    → If cache miss:
        → GET https://www.screener.in/company/{SYMBOL}/
        → Parse HTML with BeautifulSoup
        → Extract: P/E, P/B, EV/EBITDA, ROE, ROCE, D/E, rev growth, profit growth,
                   promoter holding, FII holding, latest quarterly result
        → Validate with Pydantic FundamentalData model
        → Store in fundamentals_cache table
        → Return FundamentalData
    → On scraping failure: return FundamentalData from yfinance .info as fallback
    [Satisfies: FR-02 — fundamentals field, DR-01]

  _parse_screener_page(html: str, symbol: str) -> FundamentalData
    → BeautifulSoup parsing logic
    → Each metric extracted from known CSS selectors
    → Handles missing values (returns None, not crashes)
```

#### 3.2.4 `data/indicators.py`

```
Function: compute_technical_indicators(price_history: PriceHistory) -> TechnicalIndicators
Responsibility: Compute all 8 technical indicators from OHLCV data
Depends on: pandas-ta, pandas

Logic:
  1. Convert PriceHistory to pandas DataFrame
  2. df.ta.rsi(length=14, append=True)         → RSI_14
  3. df.ta.macd(fast=12, slow=26, append=True) → MACD_12_26_9, MACDh, MACDs
  4. df.ta.bbands(length=20, append=True)       → BBL_20, BBM_20, BBU_20
  5. df.ta.ema(length=20, append=True)          → EMA_20
  6. df.ta.ema(length=50, append=True)          → EMA_50
  7. df.ta.ema(length=200, append=True)         → EMA_200
  8. df.ta.atr(length=14, append=True)          → ATR_14
  9. volume_ratio = today_volume / df['volume'].tail(20).mean()
  10. Extract latest row values into TechnicalIndicators Pydantic model
  11. Return TechnicalIndicators

Error handling: If fewer than 200 data points, EMA_200 will be None (not an error)
[Satisfies: FR-02 — technicals field]
```

#### 3.2.5 `data/news_client.py`

```
Class: NewsClient
Responsibility: RSS feed polling, storage, and retrieval
Depends on: feedparser, db/session.py

Constants:
  RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rss.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-104.rss",
    "https://www.livemint.com/rss/markets",
    "https://ndtvprofit.com/business/feed",
    "https://www.financialexpress.com/market/feed/"
  ]

Methods:
  async poll_and_store() -> int
    → For each RSS feed:
        → feedparser.parse(url)
        → For each entry: INSERT INTO news_items (deduplicate on URL)
        → Sleep 0.5 seconds between feeds
    → Delete expired items (fetched_at < NOW() - 72h)
    → Return count of new items stored
    [Satisfies: FR-13]

  async get_news_for_symbol(symbol: str, company_name: str, hours: int = 48) -> list[NewsItem]
    → SELECT from news_items WHERE published_at > NOW()-{hours}h
      AND (title ILIKE '%{company_name}%' OR title ILIKE '%{symbol}%'
           OR summary ILIKE '%{company_name}%')
    → Return up to 20 most recent matching NewsItem objects
    [Satisfies: FR-02 — news field]

  async get_google_news_rss(symbol: str, company_name: str) -> list[NewsItem]
    → Fallback if internal news DB has fewer than 3 results for a symbol
    → Queries Google News RSS: news.google.com/rss/search?q={company_name}+NSE+India
    → Returns up to 10 items (not stored, used directly)
```

#### 3.2.6 `data/context_builder.py`

```
Class: ContextBuilder
Responsibility: Orchestrates all data sources to assemble one StockContext per symbol
Depends on: all data/* modules, settings.py

Methods:
  __init__(upstox, nse, screener, news, finnhub, market_regime)
    → Stores references to all data clients

  async build(symbol: str, company_name: str, sector: str) -> StockContext
    → Runs the following CONCURRENTLY (asyncio.gather):
        [a] upstox.get_historical_ohlcv(symbol, days=60)
            → indicators.compute_technical_indicators(price_history)
        [b] nse.get_delivery_volume_pct(symbol)
        [c] nse.get_bulk_block_deals(symbol, days=7)
        [d] nse.get_insider_trades(symbol, days=30)
        [e] screener.get_fundamentals(symbol)  [cache-first]
        [f] news.get_news_for_symbol(symbol, company_name, hours=48)
        [g] finnhub.get_earnings_days_away(symbol)
        [h] nse.get_fii_dii_flows(days=7)
    → After gather: assemble StockContext with all collected fields
    → Set current_price = ohlcv[-1].close
    → Set market_regime from constructor parameter
    → Return StockContext
    [Satisfies: FR-02 — complete StockContext assembly]

  NOTE: Individual subtask failures return None for that field.
  The build() method never raises — it returns a StockContext
  with whatever data was successfully fetched. Missing fields
  are None. Models handle None gracefully in prompts.
```

---

### 3.3 Extractor Layer Module Design

#### 3.3.1 `extractors/base.py`

```python
# extractors/base.py

from abc import ABC, abstractmethod
from ..mmci.models import ModelID, ModelSignal, StockContext, Direction, Timeframe
import json
import time

class BaseExtractor(ABC):
    """
    Abstract base class for all LLM model extractors.
    Subclasses implement _call_model() to call their specific LLM.
    The base class handles retry, JSON parsing, Pydantic validation,
    and failed ModelSignal creation.
    """

    model_id: ModelID  # Must be set by subclass

    @abstractmethod
    async def _call_model(self, prompt: str) -> str:
        """Call the LLM and return raw text response."""
        ...

    async def extract(self, prompt: str, context: StockContext) -> ModelSignal:
        """
        Main extraction entry point. Called by LangGraph node.
        Returns ModelSignal(failed=True) on any error — never raises.
        """
        start_time = time.monotonic()
        for attempt in range(1, 4):  # Max 3 attempts
            try:
                raw_response = await self._call_model(prompt)
                signal = self._parse_response(raw_response, context)
                signal.latency_ms = int((time.monotonic() - start_time) * 1000)
                return signal
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == 3:
                    return self._make_failed_signal(str(e), start_time)
                await asyncio.sleep(2 ** attempt)  # 2s, 4s backoff
            except Exception as e:
                return self._make_failed_signal(str(e), start_time)

    def _parse_response(self, raw: str, context: StockContext) -> ModelSignal:
        """
        Parse raw LLM text into ModelSignal.
        Strips markdown code fences if present.
        Validates with Pydantic.
        """
        # Strip ```json ... ``` fences
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(clean)
        data["model_id"] = self.model_id
        data["raw_response"] = raw[:500]

        # Normalize direction (accept uppercase or lowercase)
        if "direction" in data:
            data["direction"] = data["direction"].upper()

        return ModelSignal.model_validate(data)

    def _make_failed_signal(self, reason: str, start_time: float) -> ModelSignal:
        return ModelSignal(
            model_id=self.model_id,
            direction=Direction.HOLD,
            confidence=0.0,
            timeframe=Timeframe.MEDIUM,
            reasoning="",
            failed=True,
            failure_reason=reason[:200],
            latency_ms=int((time.monotonic() - start_time) * 1000)
        )
```

#### 3.3.2 Extractor Implementations (Pattern — same for all 5)

```python
# extractors/gemini_pro.py

from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseExtractor
from ..mmci.models import ModelID

class GeminiProExtractor(BaseExtractor):
    model_id = ModelID.GEMINI_PRO

    def __init__(self):
        self._model = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            max_output_tokens=600
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
```

```python
# extractors/groq_qwen.py — identical pattern, different model/client

from langchain_openai import ChatOpenAI
from .base import BaseExtractor
from ..mmci.models import ModelID

class GroqQwenExtractor(BaseExtractor):
    model_id = ModelID.GROQ_QWEN

    def __init__(self):
        self._model = ChatOpenAI(
            model="qwen/qwen3-32b",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=600
        )

    async def _call_model(self, prompt: str) -> str:
        response = await self._model.ainvoke(prompt)
        return response.content
```

All 5 extractors follow this exact same pattern. Only `model_id`, `model` string, `base_url`, and `api_key` differ.

#### 3.3.3 `extractors/prompts.py`

```
Function: build_all_prompts(context: StockContext) -> dict[str, str]
  → Loads each model's prompt template from config/prompts/{model}.txt
  → Substitutes StockContext values into template
  → Returns dict: {model_id_value: prompt_string}

Function: serialize_context(context: StockContext) -> str
  → Converts StockContext to a structured text block
  → Format: clearly labelled sections (PRICE DATA, TECHNICALS,
    FUNDAMENTALS, INSTITUTIONAL FLOWS, RECENT NEWS, EVENTS)
  → Truncates news to top 10 items if more than 10 exist
  → Ensures total prompt length < 30,000 tokens (well within 1M limit)

Prompt Template Structure (for each model):
  [SYSTEM ROLE — model-specific specialization instruction]
  [STOCK CONTEXT — serialized StockContext]
  [TASK — produce JSON matching ModelSignal schema]
  [OUTPUT FORMAT — strict JSON, no markdown, no preamble]
  [JSON SCHEMA — exact field names and types]
```

---

### 3.4 LangGraph Graph (Updated Node Signatures)

#### `agents/graph.py` — Updated Node Map

```
Nodes:
  data_ingestion_node(state) → {stock_context, market_regime, run_id, started_at, errors}
    Calls: ContextBuilder.build(state["symbol"])
    Also fetches Nifty 50 regime via UpstoxClient.get_nifty50_history()

  prompt_builder_node(state) → {model_prompts}
    Calls: build_all_prompts(state["stock_context"])

  gemini_pro_node(state) → {model_signals: [signal]}    [async, in parallel superstep]
  gemini_flash_node(state) → {model_signals: [signal]}  [async, in parallel superstep]
  groq_qwen_node(state) → {model_signals: [signal]}     [async, in parallel superstep]
  groq_llama_node(state) → {model_signals: [signal]}    [async, in parallel superstep]
  deepseek_node(state) → {model_signals: [signal]}      [async, in parallel superstep]
    Each: calls extractor.extract(prompt, context), wraps in try/except

  dissent_check_node(state, defer=True) → {dissent_score, dissent_flag}
    Calls: scoring.compute_dissent_score(active_signals)

  consensus_scoring_node(state) → {consensus_score, confidence_low, confidence_high, final_direction}
    Calls: scoring.compute_consensus_score(signals, weights)
    Calls: scoring.determine_direction(S, regime)
    weights = weights_store.load_weights()

  position_sizing_node(state) → {suggested_alloc, risk_level, price_target}
    Calls: scoring.compute_position_size(S, D)
    Calls: scoring.compute_risk_level(S, D, regime)

  output_node(state) → {final_signal}
    Assembles MCISignal from all state fields

  hold_output_node(state) → {final_signal}
    Fast path for dissent override — returns MCISignal(direction=HOLD, dissent_flag=True)

Conditional routing:
  route_after_dissent(state) → "hold_output_node" | "consensus_scoring_node"
    Returns "hold_output_node" if state["dissent_flag"] is True

Graph compilation:
  builder.compile(
      checkpointer=SqliteSaver(...),  # Development
      cache=InMemoryCache()           # Node-level caching
  )
```

---

### 3.5 Auth Module (`auth/upstox_auth.py`)

```
Class: UpstoxAuthManager
Responsibility: Upstox OAuth 2.0 token lifecycle management

Attributes:
  _access_token: str | None
  _token_expiry: datetime | None
  _db_session

Methods:
  get_valid_token() -> str
    → IF token in memory and not expired → return it
    → IF token in PostgreSQL and not expired → load to memory, return it
    → IF no valid token → raise TokenExpiredError (triggers alert)
    [Satisfies: NFR-02 — daily token rotation alerting]

  async handle_notifier_callback(code: str) -> None
    → POST to Upstox token endpoint with auth code
    → Store token + expiry in PostgreSQL tokens table
    → Update in-memory token
    [Satisfies: FR — semi-automated token strategy from R2]

  is_token_valid() -> bool
    → Returns True if token exists and expires > now + 1 hour

  generate_auth_url() -> str
    → Returns the OAuth authorization URL for manual token generation

Table: tokens
  id (INT PK)
  access_token (TEXT)
  extended_token (TEXT)
  expires_at (TIMESTAMPTZ)
  created_at (TIMESTAMPTZ)
```

---

### 3.6 Database Layer (`db/models.py`)

Complete SQLAlchemy ORM definitions.

```python
# db/models.py — SQLAlchemy table definitions

from sqlalchemy import Column, String, Float, Boolean, Integer, Text
from sqlalchemy import DateTime, Date, UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class SignalRecord(Base):
    __tablename__ = "signals"

    run_id           = Column(UUID, primary_key=True, default=uuid.uuid4)
    symbol           = Column(String(20), nullable=False, index=True)
    timestamp        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    direction        = Column(String(4), nullable=False)  # BUY/HOLD/SELL
    consensus_score  = Column(Float, nullable=False)
    confidence_low   = Column(Float, nullable=False)
    confidence_high  = Column(Float, nullable=False)
    dissent_score    = Column(Float, nullable=False)
    dissent_flag     = Column(Boolean, nullable=False, default=False)
    market_regime    = Column(String(10), nullable=False)  # BULL/BEAR/SIDEWAYS
    suggested_alloc  = Column(Float, nullable=False)
    risk_level       = Column(Integer, nullable=False)
    price_target     = Column(Float, nullable=True)
    models_used      = Column(Integer, nullable=False)
    model_signals    = Column(JSONB, nullable=False)  # Full list serialized
    reasoning        = Column(Text, nullable=False)
    outcome          = Column(String(4), nullable=True)   # Filled T+5 later
    outcome_date     = Column(DateTime(timezone=True), nullable=True)
    outcome_price    = Column(Float, nullable=True)
    entry_price      = Column(Float, nullable=True)       # Price at signal time


class NewsItem(Base):
    __tablename__ = "news_items"

    id           = Column(UUID, primary_key=True, default=uuid.uuid4)
    symbol       = Column(String(20), nullable=True, index=True)  # None = market-wide
    title        = Column(Text, nullable=False)
    source       = Column(String(100), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    summary      = Column(Text, nullable=True)
    url          = Column(String(500), nullable=False, unique=True)
    fetched_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at   = Column(DateTime(timezone=True), nullable=False)


class FundamentalsCache(Base):
    __tablename__ = "fundamentals_cache"

    symbol       = Column(String(20), primary_key=True)
    data         = Column(JSONB, nullable=False)   # FundamentalData serialized
    fetched_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at   = Column(DateTime(timezone=True), nullable=False)


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id               = Column(UUID, primary_key=True, default=uuid.uuid4)
    signal_run_id    = Column(UUID, ForeignKey("signals.run_id"), nullable=False)
    symbol           = Column(String(20), nullable=False)
    direction        = Column(String(4), nullable=False)
    entry_price      = Column(Float, nullable=False)
    entry_date       = Column(Date, nullable=False)
    exit_price       = Column(Float, nullable=True)
    exit_date        = Column(Date, nullable=True)
    pnl_pct          = Column(Float, nullable=True)
    regime_at_entry  = Column(String(10), nullable=False)
    is_open          = Column(Boolean, nullable=False, default=True)


class TokenRecord(Base):
    __tablename__ = "tokens"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    access_token    = Column(Text, nullable=False)
    extended_token  = Column(Text, nullable=True)
    expires_at      = Column(DateTime(timezone=True), nullable=False)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
```

---

### 3.7 Jobs Module Design

#### `jobs/daily_analysis.py`

```
Function: async run_daily_analysis(symbols: list[str] | None = None) -> list[MCISignal]

Flow:
  1. symbols = symbols or load_watchlist_from_yaml()
  2. Validate Upstox token is valid. Raise AlertAndAbort if not.
  3. Detect market regime (Nifty 50 200-day MA check)
  4. Log: "Starting daily analysis for {len(symbols)} stocks. Regime: {regime}"
  5. Initialize ContextBuilder with all data clients
  6. Build LangGraph (compile with checkpointer + cache)
  7. For each batch of BATCH_SIZE stocks:
       For each symbol in batch (concurrent asyncio.gather):
         a. context = await context_builder.build(symbol)
         b. state = {"symbol": symbol, "model_signals": [], ...}
         c. result = await graph.ainvoke(state, config={"thread_id": f"{today}-{symbol}"})
         d. signal = result["final_signal"]
         e. Store signal to PostgreSQL
         f. Create PaperTrade if signal.is_actionable
       Sleep 60 seconds between batches (rate limit protection)
  8. Log summary: "Analysis complete. {n} signals generated. {m} actionable."
  9. Return list of MCISignal objects
```

#### `jobs/weight_updater.py`

```
Function: async update_weights_for_date(target_date: date) -> dict

Flow:
  1. target_date = date of signals to evaluate (T-5 trading days from today)
  2. Fetch all SignalRecord WHERE DATE(timestamp) = target_date
  3. For each signal:
     a. Fetch current price from Upstox
     b. Compute price_change_pct = (current_price - entry_price) / entry_price
     c. Determine actual outcome:
          BUY if price_change_pct >= +2%
          SELL if price_change_pct <= -2%
          HOLD otherwise
     d. Update SignalRecord.outcome and outcome_date in DB
     e. Update PaperTrade.exit_price, exit_date, pnl_pct, is_open=False
  4. Collect all model signals from all processed records
  5. Call WeightManager.update(all_signals, actual_outcomes)
  6. Store updated weights to LangGraph Long-Term Store
  7. Log: "Weight update complete for {target_date}. New weights: {weights}"
  8. Return new weights dict
```

#### `jobs/scheduler.py`

```python
# jobs/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

    # Daily analysis — 5:00 PM IST (post-market close)
    scheduler.add_job(
        run_daily_analysis,
        CronTrigger(hour=17, minute=0, timezone="Asia/Kolkata"),
        id="daily_analysis",
        max_instances=1,
        misfire_grace_time=3600
    )

    # News poller — every 30 minutes during market hours (9 AM – 4:30 PM IST)
    scheduler.add_job(
        news_client.poll_and_store,
        CronTrigger(
            hour="9-16", minute="*/30",
            timezone="Asia/Kolkata"
        ),
        id="news_poller"
    )

    # T+5 weight update — runs daily at 6:00 PM IST
    # Automatically determines which past date to evaluate
    scheduler.add_job(
        run_weight_update_check,
        CronTrigger(hour=18, minute=0, timezone="Asia/Kolkata"),
        id="weight_updater"
    )

    return scheduler
```

---

### 3.8 Dashboard Module (`dashboard/app.py`)

```
Streamlit Application Structure:

Page layout: Wide mode, dark theme
Sidebar: Watchlist filter, date picker, regime indicator

Main sections:
  [1] SYSTEM STATUS BAR
      Last analysis run timestamp | Next scheduled run | Any errors

  [2] TODAY'S SIGNALS TABLE
      Columns: Symbol | Direction | Score (S) | Dissent (D) | Risk | Alloc% | Regime
      Sorted by: |S| descending (highest conviction first)
      Color coding: BUY=green, SELL=red, HOLD=grey, DISSENT FLAG=orange

  [3] MODEL WEIGHT CHART
      Line chart: one line per model, last 60 days
      Shows convergence/divergence of weights over time

  [4] MODEL ACCURACY TABLE
      Columns: Model | Total Calls | Correct | Accuracy% | Current Weight
      Sorted by accuracy descending

  [5] PAPER TRADING TRACKER
      Columns: Symbol | Direction | Entry | Current | P&L% | Days Open | Regime
      Summary stats: Sharpe, Max Drawdown, Win Rate, Total P&L

  [6] GATE PROGRESS PANEL
      Visual progress bar for each of the 6 paper trading exit criteria
      Green when criterion met, red when not

Data source: Direct PostgreSQL read (SQLAlchemy)
Refresh: st.rerun() button + auto-refresh every 60 seconds
```

---

### 3.9 CLI Entry Point (`scripts/run_analysis.py`)

```python
# scripts/run_analysis.py
# Usage: python scripts/run_analysis.py [--symbols WIPRO RELIANCE TCS]

import asyncio
import argparse
from pantheon.jobs.daily_analysis import run_daily_analysis
from pantheon.db.session import init_db

async def main():
    parser = argparse.ArgumentParser(description="Run MMCI daily analysis")
    parser.add_argument("--symbols", nargs="+", help="Override watchlist symbols")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without storing to DB")
    args = parser.parse_args()

    await init_db()
    signals = await run_daily_analysis(symbols=args.symbols)

    print(f"\n{'='*60}")
    print(f"ANALYSIS COMPLETE — {len(signals)} signals generated")
    print(f"{'='*60}")
    for s in sorted(signals, key=lambda x: abs(x.consensus_score), reverse=True):
        flag = "⚠ DISSENT" if s.dissent_flag else ""
        print(f"{s.symbol:12} {s.direction.value:4} S={s.consensus_score:+.3f} "
              f"D={s.dissent_score:.3f} Alloc={s.suggested_alloc:.0%} {flag}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Part 4 — Full Database DDL

Production-ready PostgreSQL DDL. Run via Alembic migrations.

```sql
-- migration: 001_initial_schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Upstox tokens ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tokens (
    id              SERIAL PRIMARY KEY,
    access_token    TEXT NOT NULL,
    extended_token  TEXT,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── MMCI signal records ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    run_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          VARCHAR(20) NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    direction       VARCHAR(4) NOT NULL CHECK (direction IN ('BUY','HOLD','SELL')),
    consensus_score FLOAT NOT NULL,
    confidence_low  FLOAT NOT NULL,
    confidence_high FLOAT NOT NULL,
    dissent_score   FLOAT NOT NULL,
    dissent_flag    BOOLEAN NOT NULL DEFAULT FALSE,
    market_regime   VARCHAR(10) NOT NULL CHECK (market_regime IN ('BULL','BEAR','SIDEWAYS')),
    suggested_alloc FLOAT NOT NULL,
    risk_level      INTEGER NOT NULL CHECK (risk_level BETWEEN 1 AND 5),
    price_target    FLOAT,
    models_used     INTEGER NOT NULL,
    model_signals   JSONB NOT NULL,
    reasoning       TEXT NOT NULL,
    outcome         VARCHAR(4) CHECK (outcome IN ('BUY','HOLD','SELL')),
    outcome_date    TIMESTAMPTZ,
    outcome_price   FLOAT,
    entry_price     FLOAT
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_outcome ON signals(outcome) WHERE outcome IS NULL;

-- ── News items ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS news_items (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol       VARCHAR(20),
    title        TEXT NOT NULL,
    source       VARCHAR(100) NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    summary      TEXT,
    url          VARCHAR(500) NOT NULL UNIQUE,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_news_symbol ON news_items(symbol);
CREATE INDEX idx_news_published ON news_items(published_at DESC);
CREATE INDEX idx_news_expires ON news_items(expires_at);

-- ── Fundamentals cache ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fundamentals_cache (
    symbol     VARCHAR(20) PRIMARY KEY,
    data       JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- ── Paper trades ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS paper_trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_run_id   UUID NOT NULL REFERENCES signals(run_id),
    symbol          VARCHAR(20) NOT NULL,
    direction       VARCHAR(4) NOT NULL CHECK (direction IN ('BUY','SELL')),
    entry_price     FLOAT NOT NULL,
    entry_date      DATE NOT NULL,
    exit_price      FLOAT,
    exit_date       DATE,
    pnl_pct         FLOAT,
    regime_at_entry VARCHAR(10) NOT NULL,
    is_open         BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_paper_trades_open ON paper_trades(is_open) WHERE is_open = TRUE;
```

---

## Part 5 — Environment Variables Specification

Complete `.env.example` — every variable the system needs.

```bash
# .env.example — Copy to .env and fill in values

# ── LLM Providers ──────────────────────────────────────────
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
MISTRAL_API_KEY=...        # Failover only
SAMBANOVA_API_KEY=...      # Failover only

# ── Upstox ─────────────────────────────────────────────────
UPSTOX_API_KEY=...
UPSTOX_API_SECRET=...
UPSTOX_REDIRECT_URI=http://localhost:8000/callback
UPSTOX_NOTIFIER_PORT=8000

# ── Database ────────────────────────────────────────────────
DATABASE_URL=postgresql://pantheon:password@localhost:5432/pantheon
DATABASE_URL_ASYNC=postgresql+asyncpg://pantheon:password@localhost:5432/pantheon

# ── LangSmith ───────────────────────────────────────────────
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=pantheon-mmci

# ── External APIs ────────────────────────────────────────────
FINNHUB_API_KEY=...
SCREENER_EMAIL=your@email.com
SCREENER_PASSWORD=yourpassword
```

---

## Part 6 — Sprint Plan (Derived from System Design)

Six focused sprints, each producing testable, working code.

| Sprint | Duration | Deliverables | Tests |
|---|---|---|---|
| Sprint 0 | 1 day | Repo setup, DB init, `.env`, `settings.py`, `pyproject.toml` | Setup verification |
| Sprint 1 | 3-4 days | `data/` layer — all 6 data clients + `indicators.py` + `context_builder.py` | Mock API tests |
| Sprint 2 | 2-3 days | `extractors/` layer — base + 5 model adapters + `prompts.py` | Mock LLM tests |
| Sprint 3 | 2-3 days | `agents/` + `mmci/` — graph wiring + MCP evaluation (ADR-009) | Unit tests (math) |
| Sprint 4 | 2-3 days | `auth/` + `jobs/` — token management + scheduler + T+5 updater | Integration test |
| Sprint 5 | 2-3 days | `dashboard/` + CLI scripts + paper trading tracker | End-to-end test |
| Sprint 6 | 2-3 days | Backtesting module + performance metrics + paper trading gate | All AC-* tests |

**Sprint 0 starts only after:** Static IP registered with Upstox (SEBI compliance).

---

## Part 7 — Open Design Decisions (Require Evaluation During Development)

| Decision | Options | Recommended | Evaluate When |
|---|---|---|---|
| MCP data layer vs custom adapters | MCP (Upstox + OpenBB) vs direct SDK calls | MCP first (ADR-009) | Sprint 1 day 1 |
| Ollama tier (8 GB RAM) | Qwen2.5 7B only | Use as dev testing, Cerebras for production failover | Sprint 2 |
| Token refresh strategy | Manual (dev) vs semi-automated notifier | Manual for Phase 1, notifier for Phase 2 | Sprint 4 |
| Backtest data source | Upstox historical vs yfinance vs jugaad_data | Upstox primary, yfinance cross-validation | Sprint 6 |
| Fundamentals scraping rate | 2s delays vs session pooling | Start with 2s, optimize if slow | Sprint 1 |

---

*End of Document — System Design v1.0: Project Pantheon*  
*Covers: HLD, complete file structure, LLD for all 6 layers, database DDL, env spec, sprint plan*  
*Next document: Sprint 0 — Repository Setup & Initialization*
