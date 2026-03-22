# R3 — Indian Market Data Sources
## Project Pantheon Research Documentation

**Version:** 1.0  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Sources:** NSE India, BSE India, Screener.in, Finnhub, yfinance, Zerodha Pulse, feedspot — live-fetched March 21, 2026

---

## R3 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R3.1 | OHLCV Price Data Sources — Free Options | ✅ Complete |
| R3.2 | Fundamental Data Sources | ✅ Complete |
| R3.3 | News & Sentiment Data Sources | ✅ Complete |
| R3.4 | FII/DII Institutional Flow Data | ✅ Complete |
| R3.5 | Economic Calendar & Macro Data | ✅ Complete |
| R3.6 | Legal & Scraping Compliance Assessment | ✅ Complete |
| R3.7 | Python Library Ecosystem for Indian Market Data | ✅ Complete |
| R3.8 | Master Data Source Decision Matrix | ✅ Complete |
| R3.9 | Pantheon Data Architecture Recommendation | ✅ Complete |
| R3.10 | Open Items & Carry-forwards | ✅ Complete |

---

## R3.1 — OHLCV Price Data Sources

These sources provide historical and/or live Open-High-Low-Close-Volume candle data for NSE/BSE stocks. The Upstox API (R2) is already our primary source. This section covers supplementary and backup sources.

---

### R3.1.1 yfinance (Yahoo Finance Python Library)

**What it is:** Unofficial Python library that scrapes Yahoo Finance data. Uses `.NS` suffix for NSE stocks and `.BO` suffix for BSE stocks.

**Data available:**
- Historical OHLCV: Back to IPO date for most large-cap stocks (20+ years)
- Intraday data: Down to 1-minute candles for recent periods
- Basic fundamentals: P/E, P/B, EPS, market cap, dividend yield (via `.info`)
- Corporate actions: Dividends, stock splits
- Options chain (limited for India)

**Rate limits:** No official rate limit. Informal community consensus: ~2,000 requests/day before getting soft-blocked. Implement 1-second delay between calls to be safe.

**Reliability issues — CRITICAL:** yfinance has a known and persistent reliability problem for Indian stocks as of late 2025. GitHub issue #2612 (October 2025) documents `"No price data found"` errors for valid NSE symbols like `ITC.NS` and `RELIANCE.NS`. Root cause: Yahoo Finance intermittently breaks its cookie/authentication mechanism. The yfinance library updated to version 1.0 in January 2026, which resolved some issues, but this source must be treated as **supplementary only** — not a primary dependency.

**Practical use for Pantheon:**
- Backtesting historical data as a secondary check against Upstox data
- Fetching fundamentals (P/E, book value, EPS) when Screener.in is unavailable
- Use `yfinance >= 1.0` only

**Install:** `pip install yfinance` (current: v1.0, released January 24, 2026)

**Symbol format:** `RELIANCE.NS`, `TCS.NS`, `WIPRO.NS`, `ITC.NS` (NSE). `TCS.BO`, `RELIANCE.BO` (BSE).

---

### R3.1.2 jugaad_data

**What it is:** Open-source Python library that directly queries the NSE India website for historical data. No API key required.

**Data available:**
- NSE equity historical data (date range queries)
- NSE index historical data (Nifty 50, Nifty Next 50, sector indices)
- Bhav copy downloads (daily end-of-day data dump)

**Reliability:** Directly queries NSE's own web endpoints. More reliable than yfinance for Indian stocks specifically. However, NSE regularly changes its internal URLs, which can break the library temporarily.

**Rate limits:** NSE has an informal rate limit. The library already includes default delays. Keep 2-second delays between requests.

**Known issue:** Pulling more than 3-4 years of data at once often fails. Workaround: pull in 1-year chunks and concatenate.

**GitHub:** https://github.com/jugaad-py/jugaad-data  
**Install:** `pip install jugaad_data`

---

### R3.1.3 nselib

**What it is:** Python library for NSE index data specifically. Useful for Nifty 50, Nifty 500, and sector index historical data.

**Data available:**
- Historical index data for all NSE indices
- Capital market data
- Pre-open session data

**Primary use for Pantheon:** Fetching Nifty 50 historical closing prices to compute the 200-day moving average needed for market regime detection in the MMCI algorithm.

**GitHub:** Available on PyPI  
**Install:** `pip install nselib`

---

### R3.1.4 Twelve Data

**What it is:** Global market data API with Indian stock coverage (NSE).

**Free tier:** 800 API calls/day. No credit card required. Requires email registration.

**Data available:** Real-time and historical OHLCV for NSE stocks. Technical indicators computed server-side.

**Assessment for Pantheon:** Useful as a tertiary backup source. The server-side technical indicator computation (RSI, MACD, etc.) could simplify the data pipeline if Upstox + yfinance both fail.

**URL:** https://twelvedata.com  
**Symbol format:** `RELIANCE:NSE`, `TCS:NSE`

---

### R3.1.5 NSE India Official Website (Direct Scraping)

**What it is:** NSE's public website at nseindia.com exposes JSON data through its internal API endpoints that the website's front-end uses.

**Key endpoints (community-discovered, unofficial):**
- Historical data: `https://www.nseindia.com/api/historical/securityArchives`
- Market status: `https://www.nseindia.com/api/marketStatus`
- Index data: `https://www.nseindia.com/api/allIndices`
- FII/DII data: Available via the reports section

**Reliability:** NSE regularly changes these internal endpoints and adds bot protection. Requires session cookies and specific User-Agent headers. Can break with website updates. Best used via community libraries (`jugaad_data`, `stock-nse-india`) that abstract these details.

**Legal note:** NSE's ToS does not permit scraping. However, the data itself (closing prices of listed stocks) is considered public market data. This is a grey area — discussed further in R3.6.

---

## R3.2 — Fundamental Data Sources

This is the biggest gap identified in R2. Upstox API provides zero fundamental data. The following sources fill this gap.

---

### R3.2.1 Screener.in — Primary Recommended Source

**What it is:** India's most popular free stock screening and fundamental analysis website. Covers all NSE/BSE listed companies.

**Data available (per stock page):**
- P/E ratio, P/B ratio, EV/EBITDA
- ROE, ROCE, ROA
- Debt-to-equity ratio
- Revenue growth (10-year, 5-year, 3-year, TTM)
- Profit growth (same periods)
- Operating profit margin (OPM)
- Quarterly financial results (Revenue, EBITDA, PAT, EPS)
- Annual financial statements (P&L, Balance Sheet, Cash Flow)
- Shareholding pattern (Promoter, FII, DII, Public)
- Historical data going back 10+ years for most metrics

**API availability:** Screener.in has no official public API. However:
- The website serves data as structured HTML tables that are easy to parse
- A screener URL like `https://www.screener.in/company/WIPRO/` returns all fundamental data for Wipro
- Can be accessed with requests + BeautifulSoup after logging in with a free account
- A free Screener account is required to access all data (registration: name + email only)
- A Screener.in "export to Excel" button provides CSV download — automatable

**Screener.in query API (undocumented but functional):**
```
https://www.screener.in/screen/raw/?sort=&source=&order=&page=1&query=Market+Capitalization>0
```
This URL structure can be used to programmatically query and filter stocks.

**Rate limiting:** No official limits stated. Conservative approach: 1 request per 2 seconds. Screener.in has been generally tolerant of reasonable scraping for personal use.

**Account requirement:** Free registration (email + password). No payment required for basic data access.

**Assessment for Pantheon:** This is the PRIMARY source for all fundamental data. For 50 stocks, a daily scrape of Screener pages would take approximately 100 seconds at 2 seconds/request — acceptable.

---

### R3.2.2 yfinance `.info` Object — Secondary Fundamental Source

yfinance's `Ticker.info` dictionary returns a snapshot of fundamental data. Key fields available for Indian stocks:
- `trailingPE`, `forwardPE`
- `priceToBook`
- `earningsPerShare`
- `returnOnEquity`
- `debtToEquity`
- `revenueGrowth`, `earningsGrowth`
- `dividendYield`
- `marketCap`
- `sharesOutstanding`
- `sector`, `industry`

**Caveat:** Data can be stale by days or weeks. Not suitable for real-time decision making. Use as a backup or cross-validation against Screener.in.

---

### R3.2.3 BSE/NSE XBRL Filings — Raw Official Source

Both BSE and NSE now mandate XBRL (eXtensible Business Reporting Language) filings for all listed companies. Every quarterly financial result and annual report is filed in structured XBRL format.

**BSE XBRL access:** `https://www.bseindia.com/corporates/xbrldetails.aspx`

**NSE Integrated Filings:** From Q1 FY2025-26 (i.e., quarter ended March 2025 onward), financial results are available under "Integrated Filing - Financials" on NSE.

**What XBRL provides:**
- Standardized, machine-readable financial statements
- Revenue, PAT, EPS, segments, EBITDA — all tagged
- Quarterly results within days of announcement

**Practical challenge:** Parsing XBRL requires understanding the taxonomy. Python library `python-xbrl` can parse these files. This is more complex than Screener scraping but provides more authoritative data.

**Assessment for Pantheon:** Useful for the research paper (citing official exchange filings) and for the backtesting module. For real-time operations, Screener.in is simpler.

---

### R3.2.4 Tickertape & Trendlyne — Supplementary Visualization

Both Tickertape and Trendlyne are free Indian financial data portals with 200+ fundamental metrics. They do not have public APIs, but their websites are scrapable. More importantly, they serve as **human cross-validation tools** during prompt testing and signal verification.

---

## R3.3 — News & Sentiment Data Sources

---

### R3.3.1 Pulse by Zerodha — Best Free Indian News Aggregator

**What it is:** `pulse.zerodha.com` — Zerodha's free financial news aggregation service. Aggregates real-time news from all major Indian financial news sources into one feed.

**Sources aggregated:** Economic Times, Business Standard, NDTV Business, The Hindu Business, Mint, Moneycontrol, LiveMint, Financial Express, and more.

**Why it matters for Pantheon:**
- All Indian financial news in one place
- No login required
- Real-time (news appears within minutes of publication)
- Each item includes the originating source and timestamp

**Access method for Pantheon:** Pulse does not have an official API, but its news feed can be fetched. The page loads news dynamically but the underlying endpoint returns structured data. This is a priority item to investigate during the data pipeline design phase.

**URL:** https://pulse.zerodha.com

---

### R3.3.2 RSS Feeds — Reliable Free News Pipeline

RSS feeds are the most reliable, legally unambiguous way to access Indian financial news programmatically. All major Indian financial news outlets publish free RSS feeds.

**Confirmed active RSS feeds (as of March 2026):**

| Source | RSS URL | Coverage |
|---|---|---|
| Economic Times Markets | `https://economictimes.indiatimes.com/markets/rss.cms` | Broad market news |
| Moneycontrol News | `https://www.moneycontrol.com/rss/business.xml` | Business & market news |
| Business Standard Markets | `https://www.business-standard.com/rss/markets-104.rss` | Market analysis |
| NSE Official | `https://www.nseindia.com/static/rss-feed` | Corporate circulars, announcements |
| Investing.com India | `https://in.investing.com/rss/news.rss` | Global + India financial news |
| LiveMint | `https://www.livemint.com/rss/markets` | Indian market news |

**How to use in Pantheon:**
- `feedparser` Python library parses RSS feeds into structured dicts
- Schedule RSS fetch every 30 minutes during market hours
- Store headlines + summaries + timestamps in a local database
- Pass last 48h of relevant headlines to MMCI model prompts

**Legal status:** RSS is explicitly designed for machine consumption. No grey area here — all these sources publish RSS specifically for automated aggregation.

---

### R3.3.3 Finnhub — News API with Free Tier

**What it is:** Global financial data API with a generous free tier.

**Free tier limits:** 60 API calls/minute. No credit card required.

**Relevant for India:**
- `GET /news?category=general` — Global market news (includes ET, Moneycontrol articles)
- `GET /company-news?symbol=RELIANCE.NS` — Company-specific news
- NSE stocks supported via symbol change tracking endpoint
- Insider transactions for India included

**India coverage caveat:** Finnhub's news sentiment scoring (`/news-sentiment`) is confirmed US-only. Company news articles for NSE stocks are available but coverage is thinner than for US stocks.

**Assessment for Pantheon:** Use Finnhub as a supplementary news source, especially for company-specific news events. Not as comprehensive as direct RSS from Indian sources for market-wide news.

**URL:** https://finnhub.io (free API key, no credit card)

---

### R3.3.4 Google News via RSS — General News Integration

Google News has a public RSS feed feature that can be used to monitor news for any search query.

**Pattern:**
```
https://news.google.com/rss/search?q={query}+india+stock&hl=en-IN&gl=IN&ceid=IN:en
```

For example, to monitor news about Wipro:
```
https://news.google.com/rss/search?q=Wipro+NSE+stock&hl=en-IN&gl=IN&ceid=IN:en
```

**What this provides:** Aggregated news from across the Indian web for any stock or topic query. Includes articles from small regional outlets that major aggregators miss.

**Reliability:** Google News RSS has been stable for years. No authentication required. No rate limiting documented.

---

## R3.4 — FII/DII Institutional Flow Data

FII (Foreign Institutional Investors) and DII (Domestic Institutional Investors) net buying/selling data is one of the most important macro signals for Indian equities. Heavy FII selling = bearish pressure. DII buying = support.

---

### R3.4.1 NSE India Official Reports — Primary Source

NSE publishes daily FII/DII data on its website, available for free download.

**URL:** `https://www.nseindia.com/static/all-reports/historical-equities-fii-fpi-dii-trading-activity`

**Data provided:**
- Daily net purchase/sale by FII/FPI in Cash and F&O
- Daily net purchase/sale by DII in Cash
- Historical data available for several years
- Downloadable as CSV

**Access method:** The page renders data dynamically, but the underlying data endpoint can be fetched. This is a priority item to document during pipeline design.

---

### R3.4.2 SEBI Website — Authoritative but Complex

SEBI publishes FII/DII flow data in detailed reports. More authoritative than NSE's derived data but harder to parse programmatically.

**URL:** `https://www.sebi.gov.in`

**Assessment for Pantheon:** Use NSE's simplified FII/DII data for daily pipeline. Reference SEBI data only for research paper validation.

---

### R3.4.3 Moneycontrol FII/DII Page — Easy Daily Check

Moneycontrol maintains a real-time FII/DII data page that is frequently updated.

**URL:** `https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php`

**Assessment for Pantheon:** Good for human cross-validation. Can also be scraped for daily FII/DII numbers to include in MMCI model prompts as macro context.

---

## R3.5 — Economic Calendar & Macro Data

---

### R3.5.1 RBI Data Warehouse — Macro Data

The Reserve Bank of India maintains a free public data warehouse with Indian macro data.

**URL:** `https://dbie.rbi.org.in`

**Available data:**
- Repo rate, CPI, WPI inflation
- GDP growth, industrial production
- Foreign exchange reserves
- Money supply metrics

**Access:** Web interface and downloadable CSVs. No official API but pages are scrapable.

**Assessment for Pantheon:** Use for quarterly macro context in MMCI prompts. GDP and inflation data changes quarterly — one fetch per quarter is sufficient.

---

### R3.5.2 MOSPI — GDP and Statistical Data

Ministry of Statistics and Programme Implementation publishes official economic data.

**URL:** `https://mospi.gov.in`

**Assessment for Pantheon:** Same as RBI — quarterly context data. Not needed in the daily pipeline.

---

### R3.5.3 NSE India Economic Calendar

NSE publishes an economic events calendar including:
- RBI monetary policy announcement dates
- Budget presentation date
- Results announcement calendar (quarterly earnings)

**Assessment for Pantheon:** The results calendar is particularly valuable — knowing which stocks have earnings announcements in the next 7 days is essential context for the MMCI models. A stock with earnings announcement tomorrow requires a different risk assessment than one with no expected events.

---

## R3.6 — Legal & Scraping Compliance Assessment

This section documents the legal landscape for data access, directly relevant to the MMCI system.

---

### R3.6.1 NSE/BSE Data Scraping — The Legal Reality

NSE and BSE both have Terms of Service that restrict unauthorized use of their data. Their ToS typically state that data is for personal use only and cannot be used for commercial purposes or redistributed.

**However**, in Indian legal practice:
- End-of-day (EOD) price data is considered public market data
- Multiple fintech companies (Screener.in, Tickertape, Moneycontrol) access this data without formal licensing agreements for their consumer-facing products
- NSE/BSE have not taken legal action against personal finance applications that display or analyze their public market data

**Risk assessment for Pantheon:**
- Personal use (one person, no redistribution): Very low risk
- Using the data for personal investment decisions: Standard practice, no legal precedent against it
- Building a commercial product serving paying users: Requires formal data licensing from NSE/BSE or using a licensed data vendor

**Conclusion for Pantheon Phase 1:** Personal use research and signal generation is legally acceptable. When/if Pantheon becomes a commercial SaaS product, formal data licensing must be obtained.

---

### R3.6.2 Screener.in ToS

Screener.in's Terms of Service:
- Free use for personal research and analysis is permitted
- Automated scraping for commercial use or redistribution is prohibited
- The "Export to Excel" feature is explicitly provided for personal data download

**For Pantheon:** Scraping Screener.in for personal investment research and MMCI signal generation falls within acceptable use. If Pantheon becomes a commercial product, this must be revisited.

---

### R3.6.3 SEBI Algorithm Trading Regulations — Critical

**As of April 1, 2026, SEBI has introduced new algorithmic trading regulations:**

From the Breeze API documentation (ICICIdirect): *"As per SEBI regulations and the new framework, a static IP will be mandatory for API-based trading from 1st April 2026."*

This is a significant finding. As of April 1, 2026 (10 days from today), SEBI requires:
- **Static IP address** for any API-based automated trading
- API-based order placement without a static IP may be blocked by brokers

**Impact on Pantheon:**
- This regulation applies to **order placement** via API — i.e., actually buying/selling stocks automatically
- It does **not** apply to data fetching or signal generation
- Reading market data, historical prices, and portfolio holdings via API is unaffected
- Only automated order placement requires a static IP

**Action required (future):** If Pantheon ever implements automated order execution, a static IP must be configured. Most residential internet in India uses dynamic IPs. Options: VPS with static IP, or a dedicated internet connection with static IP from ISP.

**For current scope (Phase 1 — signal generation only):** No static IP required. SEBI regulation does not apply to data analysis or recommendation generation.

---

## R3.7 — Python Library Ecosystem Summary

| Library | Purpose | Install | Free? | India Coverage | Reliability |
|---|---|---|---|---|---|
| `yfinance` | OHLCV + basic fundamentals | `pip install yfinance` | Yes | Good (`.NS`/`.BO`) | Moderate (breaks occasionally) |
| `jugaad_data` | NSE historical + live data | `pip install jugaad_data` | Yes | Excellent (NSE-specific) | Good |
| `nselib` | NSE index data | `pip install nselib` | Yes | Excellent (indices) | Good |
| `feedparser` | RSS news parsing | `pip install feedparser` | Yes | Global + India RSS | Excellent |
| `finnhub` | News + some fundamentals | `pip install finnhub-python` | Free tier | Moderate | Good |
| `requests` + `bs4` | Screener.in scraping | `pip install requests beautifulsoup4` | Yes | India-specific | Good |
| `upstox-python-sdk` | OHLCV + portfolio (primary) | `pip install upstox-python-sdk` | Yes | Excellent | Official |
| `python-xbrl` | BSE/NSE XBRL filings | `pip install python-xbrl` | Yes | India-specific | Complex |

---

## R3.8 — Master Data Source Decision Matrix

For each data type MMCI needs, this table defines the primary source, backup source, and update frequency.

| Data Type | Primary Source | Backup Source | Update Frequency | Format |
|---|---|---|---|---|
| OHLCV (60-day daily) | Upstox API v3 | yfinance | Once per day (post close) | JSON → DataFrame |
| OHLCV (intraday 1-min) | Upstox API v3 | jugaad_data | Once per day (post close) | JSON → DataFrame |
| Nifty 50 index (regime detection) | Upstox API v3 | nselib | Once per day | JSON → float |
| P/E, P/B, EPS, ROE | Screener.in scrape | yfinance `.info` | Once per week | HTML → dict |
| Quarterly results | Screener.in scrape | BSE XBRL | On announcement | HTML/XBRL → dict |
| Promoter/FII shareholding | Screener.in scrape | NSE reports | Quarterly | HTML → dict |
| Company news (48h) | RSS feeds (ET, MC, BS) | Finnhub company-news | Every 30 minutes | RSS/JSON → list |
| Market-wide news | Pulse by Zerodha / RSS | Google News RSS | Every 30 minutes | RSS → list |
| FII/DII flows (daily) | NSE FII/DII reports | Moneycontrol scrape | Once per day (post close) | CSV/HTML → float |
| Earnings calendar | NSE results calendar | Screener.in announcements | Once per week | Web scrape → list |
| Macro data (CPI, repo rate) | RBI DBIE | MOSPI | Quarterly | CSV → dict |

---

## R3.9 — Pantheon Data Architecture Recommendation

Based on R3 findings, here is the recommended data layer architecture for Pantheon:

### Layer 1: Primary Market Data — Upstox API
Use the Upstox API (R2) as the sole source for all price data (OHLCV). It is free, official, reliable, and has 25 years of daily data. Do not mix price data sources to avoid inconsistencies.

### Layer 2: Fundamental Data — Screener.in + yfinance
Build a `FundamentalFetcher` that:
1. Tries Screener.in scrape first (more comprehensive, India-specific)
2. Falls back to yfinance `.info` if Screener is unavailable or slow
3. Caches results in a local SQLite or PostgreSQL database for 7 days (fundamentals don't change daily)
4. Re-fetches on quarterly results announcement days

### Layer 3: News Data — RSS Pipeline
Build a `NewsFetcher` that:
1. Polls the 6 RSS feeds listed in R3.3.2 every 30 minutes during market hours (9 AM – 4 PM IST)
2. Stores all headlines + summaries in the database with timestamps
3. At MMCI analysis time, retrieves the last 48h of news items relevant to the stock (filter by company name + sector)
4. Passes this news context to all MMCI model prompts

### Layer 4: Macro Context — Batched Weekly
Build a `MacroFetcher` that:
1. Runs once per week (Sunday night)
2. Fetches NSE FII/DII weekly aggregate
3. Fetches Nifty 50 weekly performance vs 200-day MA
4. Fetches any RBI/SEBI announcements from the past week
5. Stores as a weekly macro context object used in all that week's MMCI analyses

### Data Flow for One MMCI Analysis Run

```
MMCI Run (post-market, e.g., 4:30 PM IST)
    │
    ├─→ Upstox API:     60-day daily OHLCV for target stock
    │                   → Compute: RSI, MACD, BB, EMA 20/50/200
    │
    ├─→ Screener.in:    P/E, P/B, ROE, ROCE, quarterly result
    │                   (cached if <7 days old)
    │
    ├─→ RSS Database:   Last 48h of news items matching stock name/sector
    │                   (pre-fetched by news pipeline every 30 min)
    │
    ├─→ Macro Context:  Weekly FII/DII net flow, market regime flag
    │
    └─→ MMCI Engine:    StockContext object → 5 model calls → MCISignal
```

---

## R3.10 — Open Items & Carry-forwards

| Item | Details | Feeds Into |
|---|---|---|
| Pulse by Zerodha API endpoint | Investigate if pulse.zerodha.com has a machine-readable data feed or API endpoint | Data pipeline design |
| NSE FII/DII endpoint | Map the exact internal API endpoint on NSE website for programmatic FII/DII data | Data pipeline design |
| SEBI static IP regulation | Confirm full text of April 2026 SEBI circular. Confirm whether signal generation (not order execution) is excluded | R6 (Legal research) |
| Screener.in session handling | Test whether a free Screener.in account can maintain a persistent session for programmatic access | Pre-development testing |
| BSE XBRL parser | Evaluate `python-xbrl` complexity vs. Screener.in simplicity. Decide which is used for quarterly results ingestion | Architecture phase |
| NSE results calendar endpoint | Find the machine-readable URL for the NSE earnings announcement calendar | Data pipeline design |
| Alpha Vantage India coverage | Verify which NSE symbols Alpha Vantage covers on its free tier (25 calls/day) | Low priority backup evaluation |

---

## Summary — What R3 Gives Pantheon for Free

| Data Need | Available Free? | Best Source | Notes |
|---|---|---|---|
| Historical OHLCV (25 years) | ✅ Yes | Upstox API | Primary — already confirmed in R2 |
| Nifty 50 regime data | ✅ Yes | Upstox API / nselib | For 200-day MA computation |
| P/E, P/B, EPS fundamentals | ✅ Yes (scraping) | Screener.in | No official API; scraping is personal-use acceptable |
| Quarterly financial results | ✅ Yes (scraping) | Screener.in + BSE XBRL | XBRL is official; Screener is simpler |
| Promoter/FII shareholding | ✅ Yes (scraping) | Screener.in | Quarterly data |
| Company news (real-time) | ✅ Yes | RSS feeds + Finnhub | feedparser makes this trivial |
| Market-wide news | ✅ Yes | Pulse by Zerodha + RSS | Zerodha aggregates all Indian sources |
| FII/DII daily flows | ✅ Yes (scraping) | NSE official reports | Post-market download |
| Macro data (CPI, repo) | ✅ Yes | RBI DBIE | Quarterly |
| Earnings calendar | ✅ Yes (scraping) | NSE website | Weekly update sufficient |
| Legal right to use data | ⚠️ Personal use OK | — | Commercial use needs formal licensing |
| Static IP for order execution | ⚠️ SEBI mandate from April 2026 | VPS / static ISP | Only for automated trading; not for Phase 1 |

---

*End of Document — R3: Indian Market Data Sources*  
*Next: R4 — LangGraph Architecture Research (version compatibility, parallel fan-out support, known limitations)*
