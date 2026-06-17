# 🏛️ Project Pantheon: AI-Consensus Trading Analysis for Indian Markets

[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen.svg)]()
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status: Production-Ready](https://img.shields.io/badge/status-production--ready-success)]()

Project Pantheon is an advanced, open-source market analysis platform designed for Indian markets (NSE/BSE), combining multi-agent LLM consensus with technical, fundamental, and sentiment analytics.

---

## 📖 Architecture & Technical Stack

Pantheon operates on a highly modular, async database-centric pipeline designed to bypass commercial API limitations by utilizing free-tier AI endpoints and open data APIs.

```
                   [Real-Time Data Pipeline]
       (NSE, Upstox API, Screener, jugaad-data, News RSS)
                               │
                               ▼
            ┌───────────────────────────────────────┐
            │   MMCI (Market Mood Context Index)    │
            │  Scoring Engine (Pandas-TA, Sentiment)│
            └──────────────────┬────────────────────┘
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │    LangGraph Multi-Agent LLM        │
             │       Consensus Engine              │
             └─────────────────┬───────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────┐              ┌──────────────────────┐
│  Streamlit Dashboard │              │  Paper Trading Log   │
│   (UI visualization) │              │  (Strategy Tracker)  │
│                      │              │                      │
└──────────────────────┘              └──────────────────────┘
```

---

## 🔬 Core Engineering Features

### 1. LangGraph Multi-Agent Consensus
- Orchestrates 5+ LLMs (Gemini Flash/Pro, Groq, Ollama) using **LangGraph** state charts.
- Individual agents represent different trading personas: Technical Analyst (interprets signals), Fundamental Analyst (evaluates financials), Sentiment Analyst (reads market news), Risk Manager (enforces stop-losses).
- A **Consensus Node** synthesizes these perspectives into a unified recommendation (Buy, Sell, Hold) with a confidence percentage.

### 2. Proprietary MMCI Scoring
- **Market Mood Context Index (MMCI)** calculates a score from -1.0 to +1.0 representing overall market momentum.
- Integrates technical indicators (`pandas-ta-classic` for MACD, RSI, Bollinger Bands), fundamental scores (Screener data extraction), and real-time sentiment analysis (parsing RSS news feeds via BeautifulSoup/feedparser).

### 3. Robust Data Pipeline
- Real-time stock quotes, option chains, and index charts retrieved from the **Upstox API** and **jugaad-data** (NSE).
- Asynchronous data processing utilizing `httpx` and `asyncpg` for database writes, with caching managed via **Redis** to minimize latency.
- Non-blocking tasks scheduled via `apscheduler` to fetch index updates every 60 seconds.

### 4. Interactive Console
Streamlit-based UI displaying consensus signals, technical plots, sentiment graphs, and paper trading performance metrics.

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.11+
- PostgreSQL (Neon free tier)
- Redis instance

### Installation
1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/Pranava-Kumar/Pantheon.git
   cd Pantheon
   pip install -r requirements.txt
   ```
2. Configure your `.env` file (see `.env.example` for details):
   - PostgreSQL URL (`DATABASE_URL`)
   - Gemini & Groq API Keys
   - Upstox API Credentials
3. Run database migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the dashboard:
   ```bash
   streamlit run app.py
   ```
