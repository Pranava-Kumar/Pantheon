# Software Requirements Specification (SRS)
## Project Pantheon — Multi-Model Consensus Intelligence System

**Document Version:** 1.0  
**Date:** March 21, 2026  
**Status:** Draft — Pending Developer Review  
**SDLC Phase:** Phase 1 — Requirements  
**Derived From:** Research Tasks R1–R6 (all at v2.0)  
**Author:** [Your Name] + Claude (AI Research Assistant)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the complete functional, non-functional, data, interface, and constraint requirements for Project Pantheon — a Multi-Model Consensus Intelligence (MMCI) system for Indian equity market signal generation. It is the authoritative requirements document from which all design, implementation, and testing artifacts derive.

### 1.2 Scope

Project Pantheon is a personal investment research system that:
- Fetches market data for a watchlist of 30-40 NSE-listed stocks
- Constructs a rich contextual data object (StockContext) per stock
- Passes this context in parallel to 5 heterogeneous LLM providers
- Applies a weighted consensus algorithm to produce BUY/HOLD/SELL signals
- Learns from outcomes over time via a self-correcting weight mechanism
- Generates a research paper as a primary academic output
- Operates within SEBI regulations for personal investment use

**Explicitly out of scope for v1.0:**
- Fully automated order execution without human confirmation
- Commercial distribution of signals to paying subscribers
- Real-time intraday trading (end-of-day analysis only)
- International markets (India NSE/BSE only)

### 1.3 Definitions

| Term | Definition |
|---|---|
| MMCI | Multi-Model Consensus Intelligence — the core algorithm |
| StockContext | The structured data object assembled per stock before model calls |
| MCISignal | The final output of one MMCI analysis run for one stock |
| Superstep | A LangGraph execution unit where parallel nodes run simultaneously |
| Dissent Score (D) | Variance of signed confidence vectors across models |
| Consensus Score (S) | Weighted sum of model directional signals |
| T+5 Update | The weight adjustment job that runs 5 trading days after a signal |
| Market Regime | BULL / BEAR / SIDEWAYS — determined by Nifty 50 vs 200-day MA |
| Extended Token | Upstox API token valid 1 year (read-only portfolio APIs only) |

### 1.4 References

- R1 v2.0: Free AI Tool Ecosystem & LLM API Access Research
- R2 v1.0: Upstox API Deep Dive
- R3 v2.0: Indian Market Data Sources
- R4 v2.0: LangGraph Architecture Research
- R5 v2.0: Prior Art Survey & Novelty Claim
- R6 v2.0: SEBI Legal & Compliance Research
- NSE Circular NSE/INVG/67858 (May 5, 2025)
- SEBI Circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 (Feb 4, 2025)

---

## 2. System Overview

### 2.1 System Context

Pantheon operates as a daily post-market analysis pipeline. It is not a trading bot. It is a research and signal generation system. The human (developer) reviews signals and makes the final investment decision.

```
[Data Sources]          [Pantheon Core]           [Human + Upstox]
  Upstox API    ──→                                    │
  NSE APIs      ──→  [StockContext Builder]            │
  Screener.in   ──→         ↓                          │
  RSS/News      ──→  [MMCI LangGraph Pipeline]  ──→  Signal  ──→  Manual Order
  FII/DII Data  ──→         ↓                    Review
                     [MCISignal + Weight Update]
                             ↓
                     [PostgreSQL + LangSmith]
```

### 2.2 Operating Hours

- Analysis runs: Daily, post-market close (recommended: 5:00–6:00 PM IST)
- NSE market hours: 9:15 AM – 3:30 PM IST (Monday–Friday, excluding holidays)
- T+5 weight update job: Runs automatically 5 trading days after each signal
- News pipeline: Polls RSS feeds every 30 minutes during market hours

### 2.3 User Profile

Single user. Developer and investor. Python proficient. Uses Upstox for brokerage. Operating from Chennai, India. Using Antigravity IDE for development.

---

## 3. Functional Requirements

### FR-01: Market Regime Detection

The system SHALL classify the current market as BULL, BEAR, or SIDEWAYS by comparing the Nifty 50 closing price against its 200-day moving average.

```
BULL     if Nifty50_close > MA_200 × 1.02
BEAR     if Nifty50_close < MA_200 × 0.98
SIDEWAYS otherwise
```

The regime SHALL be computed once per analysis run and applied to ALL stocks in the watchlist for that run.

---

### FR-02: StockContext Assembly

For each stock in the watchlist, the system SHALL assemble a `StockContext` object containing:

**Price Data (from Upstox API v3):**
- 60 trading days of daily OHLCV
- Computed technical indicators: RSI-14, MACD (12/26/9), Bollinger Bands (20), EMA-20, EMA-50, EMA-200, ATR-14, Volume ratio (current/20-day avg)

**Market Microstructure Data (from NSE API/Bhav Copy):**
- Today's delivery volume as % of total volume
- Bulk deals and block deals in the last 7 calendar days
- Insider trading transactions in the last 30 calendar days
- Short selling % of total volume (today)

**Institutional Flow Data (from NSE FII/DII API):**
- FII net cash market flow — 7-day aggregate (₹ crores)
- DII net cash market flow — 7-day aggregate (₹ crores)
- FII index futures long position % (bullish/bearish indicator)

**Fundamental Data (from Screener.in — cached 7 days):**
- P/E ratio, P/B ratio, EV/EBITDA
- ROE, ROCE, Debt-to-Equity
- Revenue growth (TTM), Profit growth (TTM)
- Promoter holding % and 4-quarter trend
- Latest quarterly result summary

**News Data (from RSS pipeline — last 48 hours):**
- All headlines and summaries mentioning the company name or NSE symbol
- Source, timestamp, and link for each item
- Maximum 20 most recent articles

**Event Data (from Finnhub earnings calendar):**
- Days until next quarterly results announcement
- Any board meeting scheduled in next 14 days

**Market Context:**
- Market regime (from FR-01)
- Nifty 50 trend vs 200-day MA direction

---

### FR-03: Prompt Construction

The system SHALL build 5 model-specific prompts from the assembled StockContext. Each prompt SHALL:
- Contain the full StockContext serialized as structured text
- Include a model-specific instruction that emphasizes the model's designated analytical role
- Specify the exact JSON output schema required (matching `ModelSignal` Pydantic model)
- Include a strict instruction to return only JSON with no preamble or markdown

Model role emphasis per prompt:
- **Gemini 2.5 Pro prompt:** Macro context, geopolitical factors, qualitative reasoning
- **Gemini 2.5 Flash prompt:** Most recent news (last 24h), real-time market developments
- **Groq Qwen3 32B prompt:** Quantitative analysis, technical indicators, mathematical pattern recognition
- **Groq Llama 3.3 70B prompt:** Fundamental analysis, valuation, business quality assessment
- **DeepSeek R1 prompt:** Chain-of-thought reasoning over all available data, logical consistency check

---

### FR-04: Parallel Signal Extraction

The system SHALL call all 5 LLM models simultaneously (async parallel via LangGraph fan-out). Each model call SHALL:
- Have a maximum timeout of 20 seconds
- Retry up to 3 times on transient failures (httpx timeout, 5xx errors) with exponential backoff (2s, 4s, 8s)
- Return a `ModelSignal` object on success or a `failed=True` ModelSignal on any unhandled exception
- Never propagate an uncaught exception to the LangGraph runtime (superstep atomicity protection)

---

### FR-05: Signal Parsing and Validation

The system SHALL parse each model's JSON response into a `ModelSignal` Pydantic model containing:
- `direction`: Enum — BUY, HOLD, or SELL
- `confidence`: Float in [0.0, 1.0]
- `timeframe`: Enum — SHORT (1-5 days), MEDIUM (5-20 days), LONG (20+ days)
- `reasoning`: String ≤ 500 characters
- `price_target`: Optional float

If JSON parsing fails or Pydantic validation fails after 2 retries, the model SHALL be marked `failed=True` with the failure reason recorded.

---

### FR-06: Dissent Detection

The system SHALL compute the dissent score D as the statistical variance of signed confidence vectors:

```
D = Var({d_i × c_i})  across all active (non-failed) models
```

If D > 0.15:
- The final signal direction SHALL be overridden to HOLD
- The `dissent_flag` SHALL be set to True
- The reasoning SHALL include which models disagreed and their respective signals
- No position sizing SHALL be recommended

---

### FR-07: Consensus Scoring

If D ≤ 0.15 and at least 3 models returned valid signals, the system SHALL compute:

```
S = Σ(w_i × d_i × c_i) / Σ(w_i)
```

where `w_i` are the current dynamic weights for each model.

The system SHALL determine direction using regime-adjusted thresholds:

| Regime | θ_buy | θ_sell |
|---|---|---|
| BULL | 0.20 | -0.45 |
| SIDEWAYS | 0.30 | -0.30 |
| BEAR | 0.45 | -0.20 |

If fewer than 3 models returned valid signals, the system SHALL return HOLD with reason "INSUFFICIENT_SIGNALS".

---

### FR-08: Position Sizing

The system SHALL compute a recommended portfolio allocation percentage:

```
alloc = |S| × 0.20 × max(0.0, 1.0 - D)
```

Maximum allocation per signal: 20% of portfolio. The allocation SHALL be 0% for any HOLD or DISSENT_FLAG signal.

---

### FR-09: Risk Scoring

The system SHALL assign a risk level from 1 (low) to 5 (high):

```
base = {BULL: 1, SIDEWAYS: 2, BEAR: 3}
conviction_penalty = int((1.0 - |S|) × 2)
dissent_penalty = int(D / 0.1)
risk_level = min(5, max(1, base + conviction_penalty + dissent_penalty))
```

---

### FR-10: MCISignal Output

The system SHALL produce one `MCISignal` object per stock per run containing all fields defined in the Pydantic schema (direction, S, D, dissent_flag, regime, alloc, risk_level, timeframe, price_target, reasoning, model_signals list, models_used, run_id, timestamp, symbol).

---

### FR-11: Signal Persistence

The system SHALL store every `MCISignal` in PostgreSQL with the full `model_signals` list. The record SHALL include all fields needed for T+5 weight update evaluation. Logs SHALL be retained for a minimum of 5 years (SEBI AI/ML guideline alignment and research paper audit trail).

---

### FR-12: T+5 Weight Update

A scheduled job SHALL run 5 trading days after each signal is generated. It SHALL:
1. Retrieve the actual price change of the stock over those 5 days
2. Determine the actual outcome direction (BUY if +2%+, SELL if -2%-, HOLD otherwise)
3. For each model signal in the original run, compute `correct_i ∈ {0, 1}`
4. Apply the weight update formula with α = 0.05
5. Normalize weights to sum to 1.0
6. Apply floor (0.05) and ceiling (0.40) with soft reset if bounds violated
7. Store updated weights in LangGraph Long-Term Store

---

### FR-13: News Data Pipeline

A background job SHALL poll all 6 RSS feeds every 30 minutes during market hours (9:00 AM – 4:30 PM IST). It SHALL:
- Store all news items with title, source, timestamp, summary, and link
- Deduplicate items by URL or title similarity
- Retain items for 72 hours before deletion
- Index items by company name and NSE symbol for fast retrieval during StockContext assembly

---

### FR-14: Signal Dashboard

The system SHALL provide a Streamlit dashboard showing:
- Today's signals for all watchlist stocks (sorted by |S| descending)
- Signal history for each stock (last 30 days)
- Model weight history (line chart, one line per model)
- Accuracy metrics per model (total calls, correct, accuracy %)
- Market regime indicator
- DISSENT_FLAG count (how often consensus failed)

---

### FR-15: Paper Trading Mode

The system SHALL support a paper trading mode where:
- Each MCISignal with `is_actionable=True` is logged as a simulated trade
- P&L is computed using subsequent actual prices
- Performance metrics are tracked: Sharpe ratio, max drawdown, directional accuracy, regime-stratified returns
- The paper trading exit gate (Section 2 of Research Review Session) is tracked against all 6 criteria

---

## 4. Non-Functional Requirements

### NFR-01: Performance

- Full MMCI pipeline for one stock (from data fetch to MCISignal) SHALL complete in ≤ 45 seconds under normal conditions
- Analysis of full 35-stock pilot watchlist SHALL complete in ≤ 30 minutes total (can run in batches)
- The T+5 weight update job SHALL complete in ≤ 60 seconds regardless of watchlist size

### NFR-02: Reliability

- If any single model node fails, the system SHALL continue with remaining models (minimum 3 required)
- If fewer than 3 models respond, the system SHALL return INSUFFICIENT_SIGNALS HOLD, not crash
- If Upstox API returns an error, the system SHALL log the error and attempt yfinance fallback
- The daily token rotation failure (Upstox) SHALL trigger an SMS/email alert immediately

### NFR-03: Rate Limit Compliance

- The system SHALL never exceed Gemini 2.5 Pro's 100 RPD limit for the entire day
- The system SHALL implement token bucket rate limiting per provider
- The system SHALL log every API call with provider, model, timestamp, and token count
- Analysis SHALL be spread across the day in batches of 10 stocks, not all at once

### NFR-04: Security

- All API keys SHALL be stored in a `.env` file never committed to the Git repository
- The `.env` file SHALL be listed in `.gitignore` from day 1
- Upstox API access SHALL originate from a registered static IP address only (SEBI mandate)
- TOTP 2FA SHALL be enabled on the Upstox account
- No API keys SHALL appear in logs, error messages, or LangSmith traces

### NFR-05: Compliance

- The system SHALL operate exclusively as a personal investment research tool for the developer and immediate family
- Signals SHALL NOT be distributed to any third party without RA registration
- All MMCI signal runs SHALL be logged with full input/output data for 5-year retention
- The system SHALL operate below 10 OPS at all times (well below by design)

### NFR-06: Observability

- All LangGraph runs SHALL be traced to LangSmith (free tier: 5,000 traces/month)
- Each node execution time SHALL be logged
- All LLM API calls SHALL be logged: provider, model, tokens in/out, latency, cost
- Dashboard SHALL display system health (last successful run, next scheduled run, any errors)

### NFR-07: Maintainability

- All code SHALL include type hints (Python 3.11+)
- All modules SHALL have docstrings explaining purpose, inputs, and outputs
- Unit tests SHALL cover all MMCI scoring functions (pure math — no API calls needed)
- Test coverage SHALL be ≥ 80% on the mmci/ module
- No hardcoded values — all thresholds, weights, and configuration SHALL be in a config file

---

## 5. Data Requirements

### DR-01: StockContext Schema

All fields specified in FR-02. Pydantic model defined in `pantheon/mmci/models.py`. The expanded schema from R3 v2.0 is the authoritative field list.

### DR-02: MCISignal Schema

Pydantic model `MCISignal` already defined in the existing `models.py` file. Must be extended with the expanded StockContext fields when stored.

### DR-03: Database Schema (PostgreSQL)

**Table: signals**
- run_id (UUID, PK)
- symbol (VARCHAR)
- timestamp (TIMESTAMPTZ)
- direction (VARCHAR)
- consensus_score (FLOAT)
- dissent_score (FLOAT)
- dissent_flag (BOOLEAN)
- market_regime (VARCHAR)
- suggested_alloc (FLOAT)
- risk_level (INT)
- models_used (INT)
- model_signals (JSONB — full list)
- reasoning (TEXT)
- outcome (VARCHAR, nullable — filled by T+5 job)
- outcome_date (TIMESTAMPTZ, nullable)

**Table: model_weights (via LangGraph Long-Term Store)**
- Managed by LangGraph Store API
- Key: ("mmci", "model_weights"), namespace: "current"
- Value: dict of {model_id: weight}

**Table: news_items**
- id (UUID, PK)
- symbol (VARCHAR, nullable — null for market-wide news)
- title (TEXT)
- source (VARCHAR)
- published_at (TIMESTAMPTZ)
- summary (TEXT)
- url (VARCHAR, UNIQUE)
- fetched_at (TIMESTAMPTZ)
- expires_at (TIMESTAMPTZ — 72h after fetched_at)

**Table: paper_trades**
- id (UUID, PK)
- signal_run_id (UUID, FK → signals)
- symbol (VARCHAR)
- direction (VARCHAR)
- entry_price (FLOAT)
- entry_date (DATE)
- exit_price (FLOAT, nullable)
- exit_date (DATE, nullable)
- pnl_pct (FLOAT, nullable)
- regime_at_entry (VARCHAR)

### DR-04: Watchlist Configuration

The pilot watchlist of 30-40 stocks SHALL be stored in a configuration YAML file (`config/watchlist.yaml`). Selection criteria for the pilot:
- At least 3 stocks per major sector (IT, Banking, FMCG, Auto, Pharma, Energy, Infra)
- All large-cap (Nifty 50 or Nifty Next 50) — no mid/small-cap in Phase 1
- Exclude stocks with earnings announcement in the next 5 days at run time (too noisy)
- All must have at least 5 years of continuous NSE trading history

---

## 6. Interface Requirements

### IR-01: Upstox API Interface

- Base URL: `https://api.upstox.com/v3/`
- Authentication: OAuth 2.0 Bearer token (daily refresh)
- SDK: `upstox-python-sdk` (Python)
- Token storage: PostgreSQL `tokens` table (written by notifier URL handler)
- Fallback: yfinance if Upstox returns 5xx errors

### IR-02: LLM Provider Interfaces

All non-Google providers via `langchain_openai.ChatOpenAI` with custom `base_url`:

| Provider | Base URL | API Key Env Var |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| DeepSeek | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| Mistral | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` |

Gemini via `langchain_google_genai.ChatGoogleGenerativeAI` with `GOOGLE_API_KEY`.

### IR-03: NSE API Interface

Session-based (requests.Session with cookies). Session initialized once per run. All endpoints documented in R3 v2.0 NSE Endpoint Reference Map.

### IR-04: Screener.in Interface

Session-based scraping using requests + BeautifulSoup4. Login required (free account). 2-second delay between requests. Data cached for 7 days in PostgreSQL.

### IR-05: RSS News Interface

`feedparser` library. Six RSS feeds polled every 30 minutes. Results stored in `news_items` table. 72-hour TTL.

### IR-06: Dashboard Interface

Streamlit web application. Accessible at `http://localhost:8501` during development. Single-user, no authentication required in Phase 1. Read-only access to PostgreSQL signals and paper_trades tables.

### IR-07: LangSmith Interface

Enabled via environment variables. All LangGraph traces automatically sent. No code changes required beyond setting `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY`.

---

## 7. Constraint Catalogue

### C-01: SEBI Static IP (CRITICAL — April 1, 2026)
All Upstox API calls must originate from a registered static IP address. Register static IP with Upstox developer console before April 1, 2026.

### C-02: SEBI Personal Use Boundary
The system may only be used for the developer's own account and immediate family accounts (spouse, dependent children, dependent parents). No distribution to any third party.

### C-03: Gemini Free Tier
100 RPD on Gemini 2.5 Pro. The system must not exceed this in any single day. Caching and batching are mandatory.

### C-04: OpenRouter Quota
50 RPD without balance. Add $10 once to unlock 1,000 RPD. Treat as supplementary only.

### C-05: Rate Limit Below 10 OPS
All Upstox API order placement (Phase 3) must stay below 10 OPS per exchange per second. The system is designed for 1-5 orders per day maximum — orders of magnitude below the threshold.

### C-06: No Automatic Order Execution (Phase 1-2)
In Phase 1 and Phase 2, MMCI SHALL NOT place any orders automatically. All orders SHALL be placed manually by the human after reviewing signals. The Human-in-the-Loop design is a compliance requirement, not just a preference.

### C-07: Checkpoint Package Version
Use `langgraph-checkpoint-sqlite>=4.0.0` and `langgraph-checkpoint-postgres>=4.0.0`. Do not use 3.x versions. Schema is incompatible.

### C-08: DeepSeek Data Residency
DeepSeek processes data on Chinese servers. Do not send personal portfolio data (specific holdings, positions, account balances) in DeepSeek prompts. StockContext with public market data is acceptable.

### C-09: 5-Year Log Retention
All MMCI signal runs must be logged with full input/output data for minimum 5 years. This aligns with the SEBI AI/ML framework's expected requirement and the NSE audit trail mandate.

---

## 8. Acceptance Criteria

### AC-01: Unit Tests
All 20+ unit tests in `tests/test_mmci_core.py` pass with zero failures. These tests cover the pure math functions and require no API calls.

### AC-02: Integration Test
A full MMCI pipeline run on 3 test stocks completes without error. All 5 model nodes return valid ModelSignal objects. MCISignal is produced with all required fields populated.

### AC-03: Rate Limit Test
A simulated 35-stock analysis run stays within Gemini Pro's 100 RPD budget. Logs confirm all providers' limits were respected.

### AC-04: Failover Test
With 2 of 5 model nodes artificially failed, the system continues and produces a valid MCISignal (HOLD if dissent is high, or directional if remaining 3 models agree).

### AC-05: Weight Update Test
After a simulated T+5 outcome, weights update correctly. Models that predicted correctly gain weight. Models that predicted incorrectly lose weight. Total weight sums to 1.0. No weight falls below 0.05 or exceeds 0.40.

### AC-06: Dashboard Test
Streamlit dashboard renders without error. Signals table displays correctly. Model weight chart updates after weight update job runs.

### AC-07: Paper Trading Exit Gate (from Research Review Session)

All six criteria must be met simultaneously:
1. Sharpe Ratio ≥ 1.5
2. Max Drawdown ≤ Nifty 50's drawdown in same period
3. Directional Accuracy ≥ 55%
4. Positive alpha in ≥ 2 of 3 market regimes
5. ≥ 70% of DISSENT_FLAG signals avoided a ≥2% adverse move
6. Weight variance < 0.03 over last 30 days
7. Minimum 90 days of paper trading completed

---

## 9. Development Environment Requirements

### DE-01: Python Version
Python 3.11 or higher. 3.12 preferred.

### DE-02: Core Dependencies
```
langgraph>=1.0.0
langchain>=1.0.0
langchain-google-genai>=2.1.0
langchain-openai>=1.1.0
langgraph-checkpoint-sqlite>=4.0.0
pydantic>=2.0.0
upstox-python-sdk>=2.0.0
pandas>=2.0.0
pandas-ta>=0.3.14
feedparser>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
httpx>=0.27.0
streamlit>=1.30.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
tenacity>=8.2.0
python-dotenv>=1.0.0
loguru>=0.7.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

### DE-03: Infrastructure
- PostgreSQL 15+ (local during development, production for Phase 3+)
- Static IP from Chennai ISP or DigitalOcean Mumbai droplet (required before April 1, 2026)
- LangSmith account (free tier)

### DE-04: AI Coding Tools
- Cline (VS Code extension) — primary agentic coding tool
- Continue.dev (VS Code extension) — daily inline completion
- GitHub Copilot free tier — supplementary

---

## 10. Development Phases Overview

| Phase | Deliverable | Prerequisite |
|---|---|---|
| Phase 1 (Current) | SRS (this document) | Research complete ✅ |
| Phase 2 | System Design Document (HLD + LLD) | SRS approval |
| Phase 3 | Database Schema + Migration Scripts | System Design |
| Phase 4 | API Contract Specification | System Design |
| Phase 5 | Sprint 1: Data Pipeline (Upstox + NSE + Screener) | API Contracts |
| Phase 6 | Sprint 2: LangGraph Graph + Model Adapters | Data Pipeline |
| Phase 7 | Sprint 3: MMCI Algorithm + Tests | Model Adapters |
| Phase 8 | Sprint 4: T+5 Weight Update + Dashboard | MMCI Algorithm |
| Phase 9 | Sprint 5: Paper Trading Mode + Performance Tracking | Dashboard |
| Phase 10 | Sprint 6: Backtest Module + Research Paper Draft | All Sprints |
| Phase 11 | Paper Trading Period | All code complete |
| Phase 12 | Live Trading (after gate) + Research Paper Submission | Gate cleared |

---

## 11. Open Items

| ID | Item | Owner | Due |
|---|---|---|---|
| OI-01 | Static IP registration with Upstox | Developer | Before April 1, 2026 |
| OI-02 | Obtain all API keys (checklist in R1 v2.0) | Developer | Before Sprint 1 |
| OI-03 | Evaluate Upstox MCP server capabilities | Developer + Claude | Sprint 1 start |
| OI-04 | Finalize 35-stock pilot watchlist (sector-balanced) | Developer | Before Sprint 1 |
| OI-05 | Confirm machine RAM for Ollama tier decision | Developer | Confirmed (8 GB) |
| OI-06 | Create GitHub repository (private) | Developer | Before Sprint 1 |
| OI-07 | Set up LangSmith project "pantheon-mmci" | Developer | Before Sprint 1 |

---

*End of Document — SRS v1.0: Project Pantheon*  
*Next document: System Design Document (High-Level Design + Low-Level Design)*
