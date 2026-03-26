# Product Guide: Pantheon - Advanced Market Analysis & Trading Platform

## Vision Statement
Pantheon is an advanced, AI-driven financial analysis and trading platform designed for both Indian (NSE/BSE) and global markets. It aims to empower retail traders, algorithmic developers, and financial analysts with a consolidated, high-context environment for data-driven decision-making. By integrating real-time market data, automated news extraction, and sophisticated agentic workflows, Pantheon provides a competitive edge in market sentiment analysis and strategy execution.

## Target Audience
- **Retail Investors:** Seeking simplified yet powerful insights from diverse Indian and global data sources.
- **Algo-Traders:** Looking for robust APIs and agentic frameworks for backtesting and strategy validation across multiple exchanges.
- **Financial Analysts:** Needing automated tools for large-scale news processing and sentiment-based scoring.

## Core Goals
- **Consolidated Context:** Synthesize multiple data streams (NSE/Upstox prices, news feeds, financial reports) into a unified, actionable context for AI models.
- **Agentic Scoring (MMCI):** Utilize the Market Mood Context Index (MMCI) to autonomously score stocks based on weighted indicators across multiple dimensions.
- **Real-time Monitoring:** Provide a high-performance, interactive dashboard for tracking watchlists and strategy performance.
- **Transparent Orchestration:** Provide clear, real-time visibility into AI model execution and multi-provider fallback chains.

## Key Features
- **MMCI Scoring System:** A modular framework for calculating stock scores based on technical, fundamental, and sentiment indicators.
- **Global Market Support:** Seamless auto-detection and analysis of Indian and US/Global symbols.
- **AI News Extraction:** High-fidelity data extraction from news articles and financial reports using Google Gemini and Groq LLMs.
- **Paper Trading Tracker:** A secure environment for simulating and analyzing trades without financial risk.
- **Performance-Optimized Ingestion:** Efficient handlers for high-frequency data from NSE and Upstox to ensure low-latency insights.

## Architecture & Tech Stack Focus
- **Python-First Ecosystem:** Leveraging SQLModel for data integrity, FastAPI for high-performance services, and Streamlit for interactive UIs.
- **Agentic Frameworks:** LangChain and LangGraph for orchestrating complex analysis and scoring workflows.
- **LLM Integration:** Seamless integration with Google GenAI and Groq for advanced NLP and sentiment analysis.
