# Project Pantheon 🏛️

**Advanced AI-Powered Trading Analysis Platform for Indian Markets**

[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-production--ready-success)]()

---

## 📖 Overview

Project Pantheon is a sophisticated, **100% free and open-source** trading analysis platform that combines:

- **Multi-Model AI Consensus** - 5+ LLM models (Gemini, Groq, free tier) analyzing market signals
- **MMCI Scoring** - Proprietary Market Mood Context Index combining technical, fundamental, and sentiment analysis
- **Real-Time Data Pipeline** - NSE, Upstox, Screener integration for Indian markets
- **Paper Trading Tracker** - Risk-free strategy validation
- **Streamlit Dashboard** - Interactive visualization of signals and performance

**Built entirely with free tools:** Gemini Free Tier, Groq Free Tier, SQLite/PostgreSQL (Neon free tier), Redis (free tier), Streamlit Cloud (free)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Git
- Free API keys (see Configuration section)

### Installation

```bash
# Clone the repository
git clone https://github.com/Pranava-Kumar/Pantheon.git
cd Pantheon

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file:
```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

2. Get **FREE** API keys:

| Service | Free Tier | Sign Up |
|---------|-----------|---------|
| **Google Gemini** | 60 requests/min free | [Get Key](https://makersuite.google.com/app/apikey) |
| **Groq** | 30 requests/min free | [Get Key](https://console.groq.com/keys) |
| **Upstox** | Free market data | [Get Key](https://upstox.com/developer/) |
| **Screener.in** | Free fundamental data | [Sign Up](https://www.screener.in) |
| **Neon PostgreSQL** | Free 0.5GB database | [Get Database](https://neon.tech) |
| **Redis Cloud** | Free 30MB | [Get Redis](https://redis.com/try-free/) |

3. Update `.env` with your keys:
```env
# FREE LLM APIs
GOOGLE_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# FREE Market Data
UPSTOX_API_KEY=your_upstox_key_here
SCREENER_EMAIL=your_screener_email
SCREENER_PASSWORD=your_screener_password

# FREE Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/pantheon
DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@ep-xxx.us-east-2.aws.neon.tech/pantheon

# FREE Redis Cloud
REDIS_URL=redis://redis-xxx.us-east-1-2.ec2.redns.redis-cloud.com:xxxx

# Security (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your_generated_secret_here
```

### Run the System

```bash
# Initialize database
python -c "from pantheon.db.session import init_db; init_db()"

# Run daily analysis (all 35 watchlist stocks)
python -m pantheon.jobs.daily_analysis

# Start the API server
uvicorn pantheon.api.main:app --reload --port 8000

# Start the dashboard (in another terminal)
streamlit run pantheon/dashboard/app.py
```

Access:
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8501

---

## 📊 Features

### 1. Multi-Model AI Consensus

Five LLM models analyze each stock independently:
- **Gemini Pro** (Google) - Deep analysis
- **Gemini Flash** (Google) - Fast sentiment
- **Groq Qwen** (Alibaba) - Technical focus
- **Groq Llama** (Meta) - Fundamental focus
- **Groq GPT-OSS** (Open source) - Balanced view

**Dissent Score** measures model agreement. High dissent = HOLD signal (risk management).

### 2. MMCI Scoring System

**Market Mood Context Index** combines three dimensions:

| Dimension | Weight | Metrics |
|-----------|--------|---------|
| **Technical** | 40% | RSI, MACD, EMA, SMA, Volume |
| **Fundamental** | 30% | ROE, ROCE, Revenue Growth, Debt/Equity, PE/PB |
| **Sentiment** | 30% | LLM consensus, News sentiment, FII/DII flows |

**Output:** Score from -1.0 (strong sell) to +1.0 (strong buy)

### 3. Real-Time Data Pipeline

```
NSE/Upstox → Price Data → Technical Indicators
                      ↓
Screener.in → Fundamentals → Fundamental Score
                      ↓
News RSS → Sentiment Analysis → Sentiment Score
                      ↓
              MMCI Aggregation → BUY/HOLD/SELL
```

### 4. Paper Trading Tracker

- Automatically tracks all BUY/SELL signals
- Calculates P&L, Sharpe ratio, win rate
- T+5 day outcome evaluation
- Exit gate criteria for live trading readiness

### 5. Streamlit Dashboard

- Live signal feed
- Paper trading performance
- Market regime detection
- Model weight visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                      │
│                  (Real-time Visualization)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│  /api/v1/health  /api/v1/signals  /api/v1/trades  /trigger  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼───────┐ ┌─────▼──────┐ ┌──────▼──────┐
│   MMCI Core   │ │ Background │ │   Auth &    │
│  (Scoring)    │ │   Jobs     │ │Rate Limiting│
└───────┬───────┘ └─────┬──────┘ └──────┬──────┘
        │                │                │
┌───────▼────────────────▼────────────────▼──────┐
│              Data Layer                          │
│  SQLModel ORM │ Redis Cache │ SQLite Fallback  │
└──────────────────────────────────────────────────┘
```

---

## 📈 Performance Benchmarks

| Metric | Value | Target |
|--------|-------|--------|
| **Test Coverage** | 91 tests | 90+ ✅ |
| **API Latency (p95)** | <200ms | <200ms ✅ |
| **Daily Analysis (35 stocks)** | ~3 min | <5 min ✅ |
| **Weight Update (T+5)** | ~30 sec | <60 sec ✅ |
| **Memory Usage** | <500MB | <1GB ✅ |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_mmci_scoring_weighted.py -v
pytest tests/test_real_world_pipeline.py -v

# Run with coverage
pytest tests/ --cov=pantheon --cov-report=html
```

**Test Results:** 91 passed ✅

---

## 📝 Project Structure

```
Pantheon/
├── pantheon/
│   ├── agents/          # LangGraph state machine
│   ├── api/             # FastAPI REST API
│   ├── auth/            # JWT authentication
│   ├── config/          # Settings, watchlist, weights
│   ├── dashboard/       # Streamlit dashboard
│   ├── data/            # Data clients (NSE, Upstox, Screener, News)
│   ├── db/              # Database models, session, Redis
│   ├── extractors/      # LLM model extractors (Gemini, Groq)
│   ├── jobs/            # Background jobs (daily_analysis, weight_updater)
│   ├── mmci/            # MMCI scoring core
│   └── scripts/         # Utility scripts
├── tests/               # Test suite (91 tests)
├── conductor/           # Project management docs
├── .env.example         # Environment template
├── requirements.txt     # Dependencies
└── README.md           # This file
```

---

## 🔧 Configuration

### Model Weights (`pantheon/config/weights.yaml`)

```yaml
models:
  gemini_pro: 0.25
  gemini_flash: 0.20
  groq_qwen: 0.20
  groq_llama: 0.20
  groq_gpt: 0.15

categories:
  technicals: 0.40
  fundamentals: 0.30
  sentiment: 0.30
```

### Watchlist (`pantheon/config/watchlist.yaml`)

35 stocks across sectors:
- **IT:** WIPRO, TCS, INFY, HCLTECH, TECHM
- **Banking:** HDFCBANK, SBIN, ICICIBANK, KOTAKBANK
- **FMCG:** ITC, HINDUNILVR, NESTLEIND
- **Auto:** TMPV, MARUTI, BAJAJ-AUTO
- **Energy:** RELIANCE, ONGC, BPCL, NTPC
- **Finance:** BAJFINANCE, BAJAJFINSV
- **Pharma:** SUNPHARMA, DRREDDY, CIPLA
- **Infra:** LT, ULTRACEMCO
- **Metals:** TATASTEEL, JSWSTEEL
- **Consumer:** ASIANPAINT, TITAN

---

## 🎯 Trading Strategy

### Signal Generation

1. **Daily Analysis** (5:00 PM IST) - All 35 stocks analyzed
2. **MMCI Score** calculated for each stock
3. **Direction** determined based on market regime:
   - **BULL:** Score > 0.20 → BUY
   - **SIDEWAYS:** Score > 0.30 → BUY
   - **BEAR:** Score > 0.45 → BUY

### Risk Management

- **Dissent Flag:** If dissent score > 0.15 → HOLD (skip trade)
- **Position Sizing:** `abs(score) × 20% × (1 - dissent)`
- **Risk Level:** 1 (lowest) to 5 (highest) based on score confidence

### Outcome Evaluation (T+5)

- **BUY correct:** Price up ≥ 2% in 5 trading days
- **SELL correct:** Price down ≥ 2% in 5 trading days
- **Model weights** updated based on accuracy

---

## 📊 Performance Tracking

### Exit Gate Criteria

Before live trading, system must achieve:

| Metric | Target | Current |
|--------|--------|---------|
| Sharpe Ratio | ≥ 1.5 | Track in dashboard |
| Max Drawdown | ≤ 15% | Track in dashboard |
| Win Rate | ≥ 55% | Track in dashboard |
| Regime Coverage | 2/3 regimes | Track in dashboard |
| Trading Days | ≥ 90 | Track in dashboard |

---

## 🆓 Free Tier Deployment Guide

### Option 1: Local Development (100% Free)

```bash
# Use SQLite (no database setup needed)
DATABASE_URL=sqlite:///./pantheon.db
REDIS_URL=redis://localhost:6379/0  # Or skip Redis (falls back to in-memory)
```

### Option 2: Cloud Deployment (Free Tier)

| Service | Free Tier | Setup |
|---------|-----------|-------|
| **Database** | Neon (0.5GB free) | [neon.tech](https://neon.tech) |
| **Redis** | Redis Cloud (30MB free) | [redis.com/try-free](https://redis.com/try-free/) |
| **API Hosting** | Render/Railway (free tier) | [render.com](https://render.com) |
| **Dashboard** | Streamlit Cloud (free) | [share.streamlit.io](https://share.streamlit.io) |
| **Scheduler** | GitHub Actions (free 2000 min/month) | Built-in `.github/workflows/` |

### GitHub Actions Scheduler

Daily analysis runs automatically at 5:00 PM IST:

```yaml
# .github/workflows/daily_analysis.yml
name: Daily MMCI Analysis
on:
  schedule:
    - cron: '0 11:30 * * *'  # 5:00 PM IST
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/Pantheon.git
cd Pantheon

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests before committing
pytest tests/ -v

# Format code
black pantheon/ tests/
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **Gemini** (Google) - Free LLM API
- **Groq** - Free ultra-fast LLM inference
- **Upstox** - Free Indian market data API
- **Screener.in** - Free fundamental data
- **Neon** - Free serverless PostgreSQL
- **Streamlit** - Free dashboard hosting
- **LangChain/LangGraph** - Open-source AI orchestration

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Pranava-Kumar/Pantheon/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Pranava-Kumar/Pantheon/discussions)
- **Email:** [Contact via GitHub](https://github.com/Pranava-Kumar)

---

## 🎯 Roadmap

### Q2 2026 (Current)
- ✅ Production hardening (Redis, security, rate limiting)
- ✅ Real-world testing with March 2026 data
- ✅ Enhanced fundamental scoring (10+ metrics)
- 🔄 Backtesting framework
- 🔄 Circuit breaker monitoring

### Q3 2026
- 📅 Free LLM model integration (Ollama, HuggingFace)
- 📅 Docker containerization
- 📅 Observability (Prometheus, Grafana free tier)
- 📅 Enhanced news sentiment (Indian sources)

### Q4 2026
- 📅 Paper trading → Live trading bridge (SEBI compliant)
- 📅 Multi-asset support (Commodities, Forex)
- 📅 Advanced backtesting (Walk-forward optimization)

---

**Built with ❤️ using 100% free and open-source tools**

*Disclaimer: This is for educational purposes only. Not financial advice. Trading involves risk.*
