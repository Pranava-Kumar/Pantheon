# Tech Stack: Pantheon - Advanced Market Analysis & Trading Platform

## Core Languages & Frameworks
- **Python (Primary):** The foundational language for analysis, agents, and data engineering.
- **FastAPI:** High-performance web framework for the backend API services.
- **Streamlit:** Interactive, data-driven frontend dashboard for real-time monitoring and analysis.

## AI & Agentic Workflows
- **LangChain & LangGraph:** Orchestrating complex agentic workflows, multi-step market analysis, and the MMCI scoring process.
- **Google Gemini (GenAI) & Groq:** Primary LLM providers for financial news extraction and sentiment analysis.
- **OpenAI:** Supporting LLM services for diverse task handling and modeling.

## Financial Data & Indicators
- **Upstox SDK & jugaad-data:** Real-time and historical Indian market data (NSE/BSE) ingestion.
- **pandas & pandas-ta-classic:** High-performance data manipulation and technical indicator calculations.
- **yfinance:** Supporting global financial data and auxiliary market metrics.

## Data Persistence & Configuration
- PostgreSQL (Asyncpg/Psycopg2): Primary relational database for market data, watchlists, and scores.
- SQLModel (SQLAlchemy): Modern ORM for high data integrity and Python-native database interactions.
- Alembic: Database migrations management for maintaining a robust schema.
- PyYAML: Configuration management for model and category weights.


## Security & Authentication
- **PyJWT:** Standard JSON Web Token implementation for secure API authentication.
- **Passlib (with bcrypt):** Secure password hashing and verification logic.

## Infrastructure & Operations
- **Uvicorn:** ASGI server for high-performance FastAPI deployment.

- **APScheduler:** Automated scheduling for daily analysis, weights updates, and tracking jobs.
- **Loguru & Sentry:** Comprehensive logging and real-time error tracking.
- **Tenacity:** Robust retry logic for handling external API and network instabilities.
