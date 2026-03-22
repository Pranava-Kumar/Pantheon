# R3 — Indian Market Data Sources
## Project Pantheon Research Documentation

**Version:** 2.0 — Enhanced Second Pass  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Research Rounds:** 2 (initial pass + comprehensive second pass)  
**Sources:** NSE India archives, BSE India, PyPI, GitHub, Screener.in, Trendlyne, Tickertape, Unofficed NSE API docs, OpenBB, Pulse by Zerodha, IMARC Group, Winvesta, FindMyMoat — live-fetched March 21, 2026

---

## R3 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R3.1 | OHLCV Price Data Sources — Complete Survey | ✅ Enhanced |
| R3.2 | The NSE Python Library Ecosystem — Full Inventory | ✅ New — full library map |
| R3.3 | NSE Bhav Copy — Official EOD Data Structure | ✅ New — detailed spec |
| R3.4 | Bulk Deals, Block Deals & Insider Data | ✅ New — critical data source |
| R3.5 | Fundamental Data Sources — Comprehensive Platform Comparison | ✅ Enhanced |
| R3.6 | Screener.in — Updated Features (2025-2026) | ✅ Enhanced |
| R3.7 | Trendlyne — Full Capability Assessment | ✅ New — detailed |
| R3.8 | Tijori Finance — Alternative Data Source | ✅ New — Series A funded |
| R3.9 | BSE/NSE XBRL — Structured Quarterly Results | ✅ Enhanced |
| R3.10 | News & Sentiment Data Sources — Full Survey | ✅ Enhanced |
| R3.11 | Pulse by Zerodha — Live Confirmation | ✅ Verified live |
| R3.12 | FII/DII Institutional Flow Data — Complete Sources | ✅ Enhanced |
| R3.13 | Alternative & Non-Conventional Data Sources | ✅ New |
| R3.14 | Economic Calendar & Macro Data | ✅ Complete |
| R3.15 | OpenBB Platform — Indian Market Integration | ✅ New — significant finding |
| R3.16 | Legal & Scraping Compliance Assessment | ✅ Enhanced |
| R3.17 | Complete Python Library & Package Ecosystem | ✅ Enhanced — 20+ libraries |
| R3.18 | Master Data Source Decision Matrix | ✅ Enhanced |
| R3.19 | Pantheon Data Architecture Recommendation | ✅ Enhanced |
| R3.20 | NSE Endpoint Reference Map | ✅ New — direct API endpoints |
| R3.21 | Open Items & Carry-forwards | ✅ Updated |

---

## R3.1 — OHLCV Price Data Sources — Complete Survey

### R3.1.1 Upstox API v3 (Primary — Confirmed in R2)

The primary OHLCV source is already documented in R2. Key facts restated:
- 25 years of daily data (from January 2000)
- Intraday from January 2022 (1-minute to 300-minute intervals)
- Free with Demat account
- Official, reliable, no scraping needed
- Rate limit: 50 req/sec, 500 req/min

### R3.1.2 yfinance v1.0 (Secondary Backup)

**Current version:** 1.0 (released January 24, 2026) — major rewrite fixing many historical bugs  
**Install:** `pip install yfinance`  
**Symbol format:** `RELIANCE.NS` (NSE), `RELIANCE.BO` (BSE)

**What v1.0 fixes over 0.2.x:**
- Improved session management and cookie handling
- Better rate limit handling
- More reliable `.info` object for fundamentals
- Fewer "No price data found" errors for Indian stocks

**Data available:**
- Historical OHLCV back to IPO date
- Daily, weekly, monthly candles
- Intraday (1m, 2m, 5m, 15m, 30m, 60m, 90m) — limited lookback
- Fundamentals via `.info`: P/E, P/B, EPS, market cap, dividend yield, ROE, debt-to-equity, revenue growth, earnings growth

**Practical nuance confirmed in community testing:**
```python
import yfinance as yf
ticker = yf.Ticker("TATAMOTORS.NS")

# Historical data
hist = ticker.history(period="1y")

# Current price vs. NSE: small deviation (~0.1-0.5%) is normal
# yfinance shows 613.75 where NSE may show 613.35
# Acceptable for daily analysis; not suitable for intraday precision
```

**Known ongoing issue:** For some Indian stocks, yfinance `.info` returns missing fundamentals or stale data by several weeks. Always cross-validate against Screener.in.

**Assessment:** Excellent secondary backup. Use for historical backtesting validation and as a fallback when Upstox API is unavailable. Never as primary for live analysis.

---

### R3.1.3 jugaad_data (NSE-Specific, Highly Reliable)

**GitHub:** github.com/jugaad-py/jugaad-data  
**Install:** `pip install jugaad_data`  
**Current version:** 0.24  
**Stars:** 216 (highest-starred NSE Python library)

**Confirmed capabilities:**
```python
from jugaad_data.nse import stock_df
from datetime import date

# Fetch TATAMOTORS historical data
df = stock_df(
    symbol='TATAMOTORS',
    from_date=date(2023,1,1),
    to_date=date(2023,12,31),
    series="EQ"
)
# Returns: OPEN, HIGH, LOW, CLOSE, VOLUME, DELIVERABLE_VOLUME, DELIVERY_%

# Nifty 50 index historical
from jugaad_data.nse import index_raw
nifty_data = index_raw(symbol="NIFTY 50", from_date=date(2023,1,1), to_date=date(2024,1,1))
```

**Strengths:**
- Directly queries NSE's official endpoints
- Returns delivery volume data (what percentage of shares were actually delivered vs. speculative)
- Delivery volume is an important signal — high delivery % = more conviction buying/selling
- Data accuracy verified against NSE website in community testing

**Known limitation:** Pulling more than 3-4 years of data at once often fails. Pull in 1-year chunks and concatenate. Already documented in V1.

---

### R3.1.4 NseIndiaApi (BennyThadikaran) — NEW

**GitHub:** github.com/BennyThadikaran/NseIndiaApi  
**Install:** `pip install nseindiaapi`

A comprehensive Python wrapper for NSE's internal web API, providing:
- Equity bhav copy (daily EOD data for entire NSE universe)
- Delivery bhav copy (delivery volume data)
- Corporate actions (dividends, splits, bonus)
- NSE reports and announcements

```python
from nse import NSE
from datetime import datetime

with NSE('./') as nse:
    # Get today's bhav copy (OHLCV for entire NSE)
    bhav_file = nse.equityBhavcopy(date=datetime.now())
    
    # Get delivery data
    dlv_file = nse.deliveryBhavcopy(date=datetime.now())
    
    # Corporate actions
    actions = nse.actions()
```

**Key advantage over jugaad_data:** The bhav copy approach downloads **all stocks at once** in a single request rather than stock-by-stock. For a 50-stock watchlist analysis, a single bhav copy download is more efficient than 50 individual API calls.

---

### R3.1.5 stock-nse-india (hi-imcodeman) — NEW

**GitHub:** github.com/hi-imcodeman/stock-nse-india  
**Type:** Node.js / TypeScript library (also available as Docker container + REST API)  
**NPM install:** `npm install stock-nse-india`

**Why relevant for Pantheon:** This library exposes **all 30 NSE India API endpoints** including:
- Equity stock details and trade info
- Intraday data and historical data
- Market status and pre-open data
- Corporate announcements and circulars
- **Top gainers/losers and most active equities**
- **Option chain data**

**MCP Integration (significant finding):** The library has an integrated MCP (Model Context Protocol) client that uses AI function calling for natural language queries:
> "Access live market data, historical information, and more using plain English"

This means this library can potentially serve as an MCP tool in LangGraph for NSE data access — the same pattern as the Upstox MCP server identified in R2.

**Docker deployment:**
```bash
docker run --rm -d -p 3001:3001 imcodeman/nseindia
# Exposes REST API at http://localhost:3001
```

---

### R3.1.6 nselib (NSE Index-Specific)

**Install:** `pip install nselib`  
**Use case:** NSE index historical data (Nifty 50, Nifty 500, sector indices)

```python
from nselib import capital_market

# Nifty 500 index data for 3-year period
index_data = capital_market.index_data(
    index='Nifty 500',
    from_date='05-05-2021',
    to_date='03-05-2024'
)
```

**Primary MMCI use case:** Computing Nifty 50 200-day moving average for market regime detection. A single call to `nselib` returns the full index history needed for the regime classifier.

**Known bug:** Same 3-4 year limit as jugaad_data. Pull in 2-year chunks for longer histories.

---

### R3.1.7 Twelve Data (Tertiary Backup API)

**Free tier:** 800 API calls/day. Email registration. No credit card.  
**URL:** twelvedata.com  
**Symbol format:** `RELIANCE:NSE`, `TCS:NSE`

**Unique value for Pantheon:** Twelve Data computes **technical indicators server-side**. Instead of fetching raw OHLCV and computing RSI/MACD locally, a single API call returns the indicator value:

```
GET /rsi?symbol=RELIANCE:NSE&interval=1day&time_period=14
→ Returns: {"values": [{"datetime": "2026-03-21", "rsi": "42.3821"}]}
```

This could simplify the technical analysis layer of Pantheon's data pipeline — fewer library dependencies, server-computed indicators.

**Coverage for India:** Confirmed NSE coverage for major indices and large-cap stocks. Small and mid-cap coverage less comprehensive.

---

## R3.2 — The NSE Python Library Ecosystem — Full Inventory

Complete map of every relevant Python library for Indian stock market data, with honest reliability assessment.

| Library | Install | NSE Coverage | Active? | Primary Use |
|---|---|---|---|---|
| `upstox-python-sdk` | pip | Full NSE/BSE | ✅ Official | Primary OHLCV + portfolio |
| `yfinance` (v1.0) | pip | NSE (`.NS`), BSE (`.BO`) | ✅ Active | Secondary OHLCV + fundamentals |
| `jugaad_data` | pip | NSE historical + live | ✅ Active | Stock-level OHLCV backup |
| `nseindiaapi` | pip | Full NSE endpoint coverage | ✅ Active | Bhav copy download |
| `nselib` | pip | NSE indices | ✅ Active | Index/regime data |
| `nsepython` | pip | NSE (various) | ⚠️ Slow updates | General NSE scraping |
| `stock-nse-india` | npm | 30 NSE endpoints | ✅ Active | If using Node.js layer |
| `feedparser` | pip | RSS news parsing | ✅ Stable | News pipeline |
| `finnhub-python` | pip | Global + India | ✅ Active | News + some fundamentals |
| `requests` + `bs4` | pip | Any website | ✅ Stable | Screener.in scraping |
| `pandas` | pip | Data manipulation | ✅ Core | All data processing |
| `ta` | pip | Technical analysis | ✅ Active | RSI, MACD, BB, EMA |
| `pandas-ta` | pip | Technical analysis | ✅ Active | 130+ indicators |
| `backtrader` | pip | Backtesting | ✅ Stable | MMCI backtest module |
| `openbb` | pip | 100 data providers | ✅ Active | Optional multi-provider layer |

### The ta vs pandas-ta Decision

Both `ta` and `pandas-ta` compute technical indicators from OHLCV data. Comparison:

| Aspect | `ta` | `pandas-ta` |
|---|---|---|
| Indicators | ~40 | 130+ |
| Integration | Returns Series | Works with DataFrame directly |
| Speed | Faster | Slightly slower |
| Maintenance | Active | Active |
| Install | `pip install ta` | `pip install pandas-ta` |

**MMCI recommendation:** Use `pandas-ta` for its DataFrame integration and broader indicator coverage. MMCI needs RSI, MACD, Bollinger Bands, EMA (20/50/200), and ATR — all available in `pandas-ta`:

```python
import pandas_ta as ta
import pandas as pd

df = pd.DataFrame(ohlcv_data)
df.ta.rsi(length=14, append=True)        # RSI_14
df.ta.macd(fast=12, slow=26, append=True) # MACD_12_26_9, MACDh, MACDs
df.ta.bbands(length=20, append=True)      # BBL_20, BBM_20, BBU_20
df.ta.ema(length=20, append=True)         # EMA_20
df.ta.ema(length=50, append=True)         # EMA_50
df.ta.ema(length=200, append=True)        # EMA_200
df.ta.atr(length=14, append=True)         # ATR_14
```

---

## R3.3 — NSE Bhav Copy — Official EOD Data Structure (NEW)

The Bhav Copy (भाव कॉपी — "price copy") is the official end-of-day data file published by NSE every trading day. It is the most authoritative free source of daily market data.

### What the Bhav Copy Contains

The NSE Equity Bhav Copy is a CSV file published after market close (typically 6-7 PM IST) containing for every listed equity:
- SYMBOL, SERIES (EQ, BE, etc.)
- OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE
- TOTTRDQTY (total traded quantity = volume)
- TOTTRDVAL (total traded value)
- TIMESTAMP (trading date)
- TOTALTRADES (number of trades)
- ISIN (unique stock identifier)

### Download URL Pattern

NSE publishes bhav copies at a predictable URL:
```
https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv
```

For example, for March 21, 2026:
```
https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_21032026.csv
```

Alternative URL (older format):
```
https://www.nseindia.com/content/historical/EQUITIES/YYYY/MON/cm{DD}MON{YYYY}bhav.csv.zip
```

### Commercial vs Free Distinction

**Important finding from official NSE data page:**

NSE publishes two tiers of EOD data:
1. **Free Bhav Copy (CSV):** Available daily from the archives URL above. No subscription needed. Suitable for Pantheon's needs.
2. **End of Day data subscription (Binary format):** NSE also offers a formal commercial subscription for binary EOD files "generated in binary format at the end of each trading day" containing "bhavcopy information along with security and trade details." This requires contacting `marketdata@nse.co.in` and paying subscription fees.

For MMCI, the **free CSV bhav copy** is entirely sufficient. We do not need the commercial binary subscription.

### Delivery Volume Bhav Copy

Separately, NSE publishes delivery volume data:
```
https://www.nseindia.com/archives/equities/delhivery/MTO_{DDMMYYYY}.DAT
```

This file shows, for each stock:
- Total quantity traded
- Deliverable quantity (shares actually settled, not intraday)
- % of total trades that were deliverable

**Delivery volume is a powerful signal for MMCI:** High delivery % indicates conviction buying/selling (not just intraday speculation). This data is entirely free and published daily.

### NSE Corporate Actions File

```
https://www.nseindia.com/archives/equities/mas/MA{DDMMYYYY}.csv
```

Contains: dividends, bonus issues, stock splits, rights issues, face value changes — all of which affect the price series and must be accounted for in backtesting.

---

## R3.4 — Bulk Deals, Block Deals & Insider Data (NEW)

This is a critically underutilized data category for MMCI. Bulk and block deals reveal what large institutional investors are actually doing — not what they say they're doing.

### Definitions

**Bulk Deal:** Any transaction where total shares traded exceed 0.5% of the listed company's total equity shares. Disclosed same day after market hours. NSE + BSE both publish this data.

**Block Deal:** A single transaction of minimum 500,000 shares OR minimum ₹5 crore value, executed in a separate trading window (opens 8:45-9:00 AM before regular market hours). Disclosed same day.

**Insider Trading Disclosures:** SEBI mandates disclosure when promoters, KMP, or directors transact in company shares. Filed with BSE/NSE within 2 trading days of the transaction.

### Why This Matters for MMCI

Bulk and block deal data is a leading indicator:
- FII bulk buying of a stock = strong foreign institutional conviction = potential BUY signal
- Mutual fund bulk selling = institutional exit = potential SELL signal
- Insider buying = management confidence in company prospects
- Insider selling = could indicate information asymmetry

Including bulk/block deal and insider transaction data in the StockContext object passed to MMCI models would significantly enrich the analysis beyond technical indicators and news.

### Free Data Access Methods

**NSE Official API Endpoint (community-discovered):**
```python
# NSE Large Deal API — returns bulk deals, block deals, short selling
import requests
session = requests.Session()
session.get("https://www.nseindia.com")  # Required to set cookies

# Today's bulk deals
bulk_deals = session.get(
    "https://www.nseindia.com/api/snapshot-capital-market-largedeal",
    params={"type": "bulk_deals", "view": "mode"}
).json()

# Historical bulk deals
historical = session.get(
    "https://www.nseindia.com/api/snapshot-capital-market-largedeal",
    params={
        "type": "bulk_deals",
        "from_date": "15-01-2026",
        "to_date": "21-03-2026"
    }
).json()
```

**Via NSEIndiaApi Python library:**
```python
from nse import NSE
with NSE('./') as nse:
    bulk_deals = nse.equityBulkDeals()
    block_deals = nse.equityBlockDeals()
```

**Via nsepython library:**
```python
from nsepython import nse_largedeal
bulk_data = nse_largedeal(
    bandtype="bulk_deals",
    from_date="15-01-2026",
    to_date="21-03-2026"
)
```

**BSE Bulk Deals:** Available at `https://www.bseindia.com/data/xml/notices.xml` and via the BSE bulk deals page downloadable as CSV.

**Historical coverage:** Data available from January 2015 (NSE) and similar date range (BSE). This gives over a decade of institutional flow data for backtesting.

### Insider Trading Data

```python
# NSE insider trading endpoint
insider_data = session.get(
    "https://www.nseindia.com/api/corporates-pit",
    params={"index": "equities", "symbol": "WIPRO"}
).json()
```

BSE publishes insider trading disclosures at:
```
https://www.bseindia.com/data/xml/notices.xml
```

### SEBI SAST Disclosures (Substantial Acquisition)

When any entity acquires more than 5% of a company, SEBI SAST (Substantial Acquisition of Shares and Takeovers) mandates disclosure. These are filed with BSE/NSE and publicly available. Useful for detecting upcoming M&A or promoter stake changes.

---

## R3.5 — Fundamental Data Sources — Full Platform Comparison

The V1 document covered Screener.in as the primary source. The second pass reveals a richer ecosystem with distinct strengths.

### The Indian Fundamental Data Landscape (March 2026)

| Platform | Free Tier | Parameters | Data Depth | Programmatic Access | SEBI Registered? |
|---|---|---|---|---|---|
| Screener.in | Yes (limited) | ~50 core metrics | 10+ years | Scraping only | No |
| Trendlyne | Yes (basic) | 1,400+ (3,000+ premium) | 10+ years | API on premium | ✅ INH000022507 |
| Tickertape | Yes | 100+ | Good | Broker integration only | No |
| Tijori Finance | Limited free | 6,000+ operational metrics | Annual reports | API (paid) | No |
| yfinance `.info` | Yes | ~40 metrics | Variable | Direct Python | No |
| Moneycontrol | Yes | Comprehensive | Good | Scraping | No |
| BSE XBRL | Yes (official) | All financial statement items | Quarterly filings | Direct download | Official |

---

## R3.6 — Screener.in — Updated Features (2025–2026)

V1 covered Screener.in's core features. The second pass reveals several important updates.

### New Features (2025-2026)

1. **Commodity price trend analysis (new):** Covers 10,000+ commodities. Useful for sector-specific analysis — e.g., steel company valuations correlated with iron ore prices.

2. **Shareholder search functionality (new):** Identify all companies where a specific person or institution owns more than 1% of shares. Useful for tracking "super investor" portfolios (Vijay Kedia, Porinju Veliyath, etc.).

3. **Screener AI credits (premium):** ₹500 of AI credits included in premium plan for extracting insights from company documents.

### Pricing Update (2025-2026)

- **Free tier:** Core fundamental data, limited screens
- **Premium:** ₹4,999/year
  - Unlimited company tracking
  - 800 stock alerts + 75 screen alerts
  - Detailed peer comparisons
  - Excel automation with custom templates
  - Industry filters
  - ₹500 AI credits

### Screener.in Programmatic Access — Updated Methods

**Method 1: Direct URL scraping (most reliable)**
```python
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
}
session = requests.Session()

# Login with free account
session.post(
    "https://www.screener.in/login/",
    data={"username": "your@email.com", "password": "yourpassword"}
)

# Fetch company page
response = session.get("https://www.screener.in/company/WIPRO/")
soup = BeautifulSoup(response.text, 'html.parser')

# Extract key metrics from the structured HTML
# P/E ratio, P/B, ROE, ROCE, Debt/Equity, etc.
```

**Method 2: Screener query API**
```
https://www.screener.in/screen/raw/?sort=&source=&order=&page=1&query=Market+Capitalization>0
```
Returns stocks matching query criteria — can be used to build watchlists.

**Method 3: Excel export automation**
Screener's premium "Excel Connect" feature allows scheduled data pulls into Excel/Google Sheets. While this is a GUI feature, the underlying HTTP endpoint can be automated.

### Critical Limitation Update

V1 noted Screener.in has no official API. This remains true in March 2026. The scraping approach works but requires:
- Session maintenance with cookies
- A free Screener account
- 2-second delays between requests
- Regular testing because Screener updates its HTML structure periodically

---

## R3.7 — Trendlyne — Full Capability Assessment (NEW)

V1 mentioned Trendlyne briefly. The second pass reveals it is significantly more powerful than initially assessed and warrants serious consideration.

### Why Trendlyne Matters for Pantheon

Trendlyne is **SEBI-registered (INH000022507)** — it is a registered Research Analyst, not just a data tool. This means the data quality it provides meets regulatory standards.

### Unique Data Points Not Available Elsewhere Free

1. **Consensus Estimates ("Forecaster"):** Analyst forward revenue, EPS, profit, dividends, cash flow, capex estimates — both historical and real-time. This is institutional research data typically behind expensive paywalls.

2. **DVM Score:** Proprietary Durability-Valuation-Momentum score (0-100 on each dimension). Backtesting shows high DVM stocks consistently outperform. This pre-computed score could be a direct input to MMCI model prompts.

3. **Real-time screener alerts:** Screener alerts refreshing every 15 minutes on premium tier. No equivalent on Screener.in (EOD only).

4. **1,400+ screener parameters:** vs. ~50 on Screener.in free. Includes institutional data, insider trades, and alternative metrics.

5. **Superstar investor portfolios:** Track portfolios of ace investors (Vijay Kedia, Rakesh Jhunjhunwala estate, Dolly Khanna, etc.) — updated quarterly after shareholding pattern disclosures.

### Trendlyne Pricing (Updated 2025-2026)

| Plan | Monthly | Annual | Key Features |
|---|---|---|---|
| Basic | ₹119 | ₹1,190 | Core screener, basic alerts |
| StratQ | ₹491 | ₹5,900 | 200 watchlists, 1,200 backtests, Excel Connect, unlimited data downloads |
| Pro Global | ₹741 | ₹8,900 | US stocks added |
| Pro Plus Global | ₹991 | ₹11,900 | Full India + US features |

**For Pantheon research phase:** Free tier is sufficient to validate data quality. For production, StratQ at ₹491/month provides Excel Connect (automation-friendly) and unlimited downloads.

### Trendlyne Programmatic Access

Trendlyne has a documented Excel Connect API for premium subscribers. The data flows through structured endpoints that can be accessed programmatically. On the free tier, scraping the website works similarly to Screener.in.

**High-value endpoint for MMCI:** Trendlyne's consensus estimates (analyst forward EPS) can be included in the `FundamentalData` object passed to MMCI models — specifically, the discrepancy between current P/E and forward P/E based on analyst estimates is a strong directional signal.

---

## R3.8 — Tijori Finance — Alternative Data Source (NEW)

**Status:** Raised $9.28M in Series A funding (November 2025) — active and growing

**Website:** tijorifinance.com

Tijori Finance takes a fundamentally different approach to Indian fundamental data: instead of aggregating standardized financial statement items, it extracts **operational metrics** directly from annual reports, management commentary, and investor presentations.

### What Tijori Covers That Others Don't

**6,000+ operational metrics not available on other platforms:**
- Market share data (company-specific, extracted from annual reports)
- Revenue mix breakdowns (product-wise, geography-wise, customer concentration)
- Store counts, capacity utilization, fleet size
- Supply chain information
- Unit economics (where disclosed)
- Management guidance tracking (what management said vs. what happened)

### Why This Matters for MMCI

The models in MMCI receive fundamentals from the `FundamentalData` object. Currently, this object contains standard financial ratios (P/E, ROE, etc.). Tijori's operational metrics would allow passing much richer context:

- "Wipro's cloud revenue grew 23% YoY according to their Q3 FY26 report"
- "ITC's FMCG segment contribution reached 42% of revenues, up from 38%"

This is exactly the kind of differentiated context that allows MMCI models to reason beyond surface-level financials.

### Access Model

Tijori has a limited free tier and paid API. Given the Series A funding, an API will likely expand. For Pantheon Phase 1, manual cross-referencing with Tijori is the realistic approach. For Phase 4 (commercial), a Tijori data partnership is worth exploring.

---

## R3.9 — BSE/NSE XBRL — Structured Quarterly Results (Enhanced)

### The XBRL Landscape for India

BSE was the **first stock exchange in India** to implement XBRL-based reporting, starting with shareholding patterns and financial results. NSE followed with "Integrated Filing - Financials" from Q1 FY2025-26.

**What is covered in XBRL filings:**
- Standalone and consolidated quarterly P&L (Revenue, EBITDA, PAT, EPS)
- Balance sheet items (quarterly)
- Segment information
- Audit observations
- Shareholding pattern (promoter, FII, DII, public)

### BSE XBRL Access

**URL:** `https://www.bseindia.com/corporates/xbrldetails.aspx`

BSE provides a "Consolidated Detailed Quarterly financial result" in XBRL format accessible online. Structured machine-readable data.

**Programmatic access:**
```python
# BSE publishes quarterly results announcements via their listing center
# Financial results are accessible at:
# https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?
#   strCat=Financial Results&strPrevDate=&strScrip={SCRIP_CODE}
#   &strSearch=P&strToDate=&strType=C&subcategory=Annual Report

# Example: Wipro BSE scrip code is 507685
url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
params = {
    "strCat": "Financial Results",
    "strScrip": "507685",
    "strSearch": "P",
    "strType": "C",
    "subcategory": "Annual Report"
}
```

### Python XBRL Parsing Library

The `python-xbrl` library (PyPI) parses XBRL documents from Indian exchange filings. The parsing is complex but the library handles the taxonomy mapping.

**Simpler alternative:** The BSE API already returns structured JSON for most financial data without needing XBRL parsing. Use XBRL only for deeply granular segment-level data not available in the JSON API.

### NSE Integrated Filing (New from Q1 FY2025-26)

From the quarter ended June 2025 onwards, NSE mandates "Integrated Filing - Financials" where listed companies submit results in a standardized JSON format directly on NSE's portal. This new format is significantly more programmatic-friendly than the previous PDF/Excel submissions.

**Implication:** For data after Q1 FY2025-26 (July 2025 onwards), NSE's integrated filing endpoint will be more reliable for quarterly results than scraping Screener.in. This is a significant improvement to document for Pantheon's data pipeline design.

---

## R3.10 — News & Sentiment Data Sources — Full Survey

### R3.10.1 Pulse by Zerodha — Confirmed Live (March 21, 2026)

Pulse is confirmed operational and publishing news as of today (March 21, 2026). Live snapshot from today's feed includes:

- Middle East energy strike news driving crude above $116/barrel
- ITC Hotels demerger coverage
- NSE F&O contract exclusions
- Indian rupee falling past ₹93 vs USD (Strait of Hormuz geopolitical risk)
- RBI intervention commentary
- Income Tax Rules 2026 gazette notification

This is exactly the kind of real-time macro + sector-specific news that MMCI models need. Pulse aggregates from: NDTV Business, Economic Times, The Hindu Business, LiveMint, and more — all in one feed.

**Programmatic access investigation:** Pulse is at `pulse.zerodha.com`. The website loads news dynamically. Community tools exist that use its RSS feed-style data. The underlying endpoint to investigate:
```
https://pulse.zerodha.com/
```

The news items appear to load via a JSON API. During development, investigate the browser network requests on pulse.zerodha.com to identify the exact JSON endpoint — this is a better approach than scraping the HTML.

### R3.10.2 RSS Feeds — Complete & Verified List

**Primary Indian Financial News RSS Feeds (verified active March 2026):**

| Source | RSS URL | Update Frequency | Coverage |
|---|---|---|---|
| Economic Times Markets | `https://economictimes.indiatimes.com/markets/rss.cms` | Real-time | Broad market + company news |
| Moneycontrol Business | `https://www.moneycontrol.com/rss/business.xml` | Real-time | Business + market |
| Business Standard Markets | `https://www.business-standard.com/rss/markets-104.rss` | Real-time | Market analysis |
| LiveMint Markets | `https://www.livemint.com/rss/markets` | Real-time | Indian market news |
| NDTV Profit | `https://ndtvprofit.com/business/feed` | Real-time | Business news |
| Financial Express Market | `https://www.financialexpress.com/market/feed/` | Real-time | Market data + analysis |
| Investing.com India | `https://in.investing.com/rss/news.rss` | Real-time | Global + India |
| NSE Circulars | `https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_RSS_CIRCULARS.xml` | As published | Official exchange circulars |

**Python RSS pipeline:**
```python
import feedparser
import time

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rss.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-104.rss",
    "https://www.livemint.com/rss/markets",
]

def fetch_all_news(keywords: list[str]) -> list[dict]:
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if any(kw.lower() in entry.get("title","").lower() 
                   or kw.lower() in entry.get("summary","").lower() 
                   for kw in keywords):
                articles.append({
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "published": entry.get("published"),
                    "source": feed.feed.get("title"),
                    "link": entry.get("link")
                })
        time.sleep(0.5)  # Polite delay
    return articles
```

### R3.10.3 Google News RSS — Stock-Specific Feeds

Google News provides RSS feeds for any search query:
```
https://news.google.com/rss/search?q={QUERY}&hl=en-IN&gl=IN&ceid=IN:en
```

For MMCI, per-stock feeds are extremely valuable:
```python
import urllib.parse

def get_google_news_rss(company_name: str, nse_symbol: str) -> str:
    query = urllib.parse.quote(f"{company_name} OR {nse_symbol} NSE stock India")
    return f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

# Usage
wipro_rss = get_google_news_rss("Wipro", "WIPRO")
# Returns: articles from ALL sources mentioning Wipro in Indian financial context
```

This is the most complete per-stock news source because Google News aggregates from hundreds of Indian outlets, including regional ones that major aggregators miss.

### R3.10.4 NSE Announcements RSS

NSE publishes official company announcements (corporate actions, board meeting notices, results dates, insider trading) via RSS:

```
# NSE company announcements
https://www.nseindia.com/api/corporates-announcements?index=equities&symbol=WIPRO
```

This is more reliable than news articles for structured corporate events:
- Results announcement dates
- Board meeting dates
- Dividend announcements
- Stock split/bonus notices
- AGM notices

Integrate this into the Pantheon news pipeline alongside RSS feeds.

### R3.10.5 Finnhub — Updated Assessment

**Free tier:** 60 API calls/minute. No credit card.

```python
import finnhub
client = finnhub.Client(api_key="YOUR_KEY")

# Company news for Indian stock
news = client.company_news("WIPRO.NS", _from="2026-03-14", to="2026-03-21")

# Market news (includes major Indian news)
market_news = client.general_news("general", min_id=0)
```

**India coverage assessment (March 2026):** Finnhub's company-specific news for NSE stocks has improved since 2024. Coverage is reasonable for large-cap Nifty 50 stocks. Less reliable for mid and small-cap stocks.

**Key Finnhub feature for MMCI:** Finnhub's `earnings_calendar` endpoint returns upcoming quarterly results dates globally, including Indian companies. This is the most reliable programmatic source for the NSE earnings calendar:

```python
# Earnings calendar for Indian stocks
from datetime import date, timedelta
earnings = client.earnings_calendar(
    _from=str(date.today()),
    to=str(date.today() + timedelta(days=30)),
    symbol="",
    international=True  # Include non-US markets
)
# Filter for .NS symbols to get NSE earnings calendar
nse_earnings = [e for e in earnings.get("earningsCalendar",[]) if e.get("symbol","").endswith(".NS")]
```

---

## R3.11 — FII/DII Institutional Flow Data — Complete Sources

### Primary Source: NSE Official FII/DII Data

NSE publishes daily FII/DII activity data through multiple endpoints:

**Via NSE website:** `https://www.nseindia.com/static/all-reports/historical-equities-fii-fpi-dii-trading-activity`

**Via NSE API (community-discovered):**
```python
# NSE FII/DII stats API endpoint
fii_dii_data = session.get(
    "https://www.nseindia.com/api/fiidiiTradeReact"
).json()
# Returns: cash market FII/DII net buy/sell for current day
```

**Historical FII/DII data:**
The NSE report page allows date-range downloads of FII/DII data. Community tools automate this via the NSE internal API.

### Secondary Sources

| Source | Update | Format | Notes |
|---|---|---|---|
| NSE FII/DII API | Real-time during market hours | JSON | Most current |
| NSE Historical Reports | Daily, post-close | CSV download | Complete historical |
| Moneycontrol FII/DII page | Real-time | Web (scrapable) | Easy to scrape |
| NSE India Bulk Deals page | Post-market | CSV + JSON | Stock-level FII transactions |
| SEBI FPI Holdings Portal | Monthly | PDF/CSV | Detailed FII holdings by stock |

### FII Derivative (F&O) Activity — Separate Signal

In addition to cash market FII activity, NSE publishes FII participation in F&O:
- FII Long positions in index futures (bullish signal)
- FII Short positions in index futures (bearish signal)
- FII Put/Call ratio in index options

**Endpoint:**
```
https://www.nseindia.com/api/reportsFiiDii
```

**Why this matters:** The FII F&O data is often a leading indicator of cash market direction. Heavy FII short-building in Nifty futures frequently precedes cash market declines. Including this in the MMCI macro context significantly enriches the analysis.

---

## R3.12 — Alternative & Non-Conventional Data Sources (NEW)

This section covers non-standard data types that can enrich MMCI's analysis beyond standard OHLCV + fundamentals + news.

### R3.12.1 The India Alternative Data Market Context

India's alternative data market reached **$290.50 Million in 2024** and is projected to reach **$4,385.41 Million by 2033** (CAGR: 35.2%). MoSPI hosted a brainstorming session in March 2025 to integrate non-conventional data — including satellite imagery, telecom records, and social media — with traditional statistics.

This is not just a global trend — it is now a policy-level priority in India.

### R3.12.2 Free/Low-Cost Alternative Data Available for MMCI

**Satellite/Weather Data (sector-relevant):**
- NOAA weather data (free) correlates with agricultural commodity prices and FMCG sector demand
- Sentinel satellite imagery (free, EU Copernicus program) can proxy construction activity, retail parking lot occupancy
- Relevant for specific sector analyses (FMCG, Agriculture, Real Estate)

**Consumer Sentiment:**
- Google Trends India: Tracks search volume for company brands, products
  - `https://trends.google.com/trends/explore?geo=IN&q=Wipro+jobs` — job search volume = business activity proxy
  - Free, no authentication required
  - `pytrends` Python library for programmatic access

**Social Media Sentiment:**
- Twitter/X India financial community discussion of stocks
- Reddit (r/IndiaInvestments) — retail investor sentiment
- Both are accessible without paid APIs for volume/sentiment estimation

**App Ratings and Downloads:**
- Play Store ratings for fintech companies, banks, e-commerce
- Proxy for consumer satisfaction and brand health
- Available from AppFollow, Sensor Tower (paid) or manual via Google Play scraping

### R3.12.3 MCA21 (Ministry of Corporate Affairs)

MCA21 is India's official corporate registration database. All registered companies must file annual returns and financial statements here.

**URL:** `https://www.mca.gov.in/content/mca/global/en/data-and-reports/company-master-data.html`

**Relevant data:** Director information, charges (debt), annual returns, ROC filings

**Why relevant for MMCI:** For unlisted group companies of listed entities, MCA21 provides financial health data not available elsewhere. Also useful for detecting undisclosed related-party transactions.

**Access:** Free download of company master data (CSV). Individual company filings require account registration (free).

### R3.12.4 NSE Short Selling Data

NSE publishes daily short-selling data — which stocks are being heavily shorted:
```python
short_selling = session.get(
    "https://www.nseindia.com/api/snapshot-capital-market-largedeal",
    params={"type": "short_sell", "view": "mode"}
).json()
```

High short interest in a stock is both a bearish signal (smart money bets down) and a contrarian indicator (short squeeze potential). Including this in MMCI's StockContext adds a dimension no current multi-agent trading system uses.

---

## R3.13 — Economic Calendar & Macro Data

### RBI DBIE (Primary)

**URL:** `https://dbie.rbi.org.in`  
**Coverage:** Repo rate, CPI, WPI, GDP, forex reserves, money supply  
**Update frequency:** Monthly (inflation), Quarterly (GDP)  
**Access:** Free download (CSV), no authentication required

### MOSPI (Secondary)

**URL:** `https://mospi.gov.in`  
**Coverage:** Official GDP, Index of Industrial Production (IIP), Consumer Price Index  
**Access:** Free publications, downloadable data

### NSE Earnings Calendar

NSE publishes a board meeting and results announcement calendar:
```python
# NSE corporate board meetings and results dates
upcoming = session.get(
    "https://www.nseindia.com/api/corporate-board-meetings",
    params={"index": "equities", "from_date": "01-04-2026", "to_date": "30-06-2026"}
).json()
```

**For MMCI:** Knowing which stocks have earnings announcements in the next 7 days changes the risk assessment dramatically. A stock with results in 2 days requires a HOLD bias regardless of technical signals.

### RBI Policy Calendar

The RBI publishes its monetary policy committee (MPC) meeting schedule for the entire fiscal year in advance. These dates are high-impact market events:
- Repo rate decisions move the banking sector significantly
- Liquidity announcements affect broad market direction

**Source:** `https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx`

Available as structured HTML that can be scraped or manually entered into a static calendar.

---

## R3.14 — OpenBB Platform — Indian Market Integration (NEW)

### What OpenBB Is

OpenBB Platform (current version: 4.7.1 as of March 2026) is an **open-source, free financial data platform** that integrates with nearly 100 different data providers under a single standardized Python API.

**License:** GNU AGPLv3 (open-source, free to use)  
**GitHub:** github.com/OpenBB-finance/OpenBB

### The Key Value Proposition

Instead of writing separate integration code for yfinance, Twelve Data, Finnhub, Alpha Vantage, and others, OpenBB provides a **single unified interface**:

```python
from openbb import obb

# Same command, different providers
historical_yfinance  = obb.equity.price.historical("RELIANCE.NS", provider="yfinance")
historical_twelvedata = obb.equity.price.historical("RELIANCE:NSE", provider="twelvedata")

# Standardized output format regardless of provider
df = historical_yfinance.to_dataframe()
```

### OpenBB MCP Integration (Significant for Pantheon Architecture)

OpenBB Platform 4.7.1 includes a built-in **MCP server**:
```python
# OpenBB exposes its entire financial data API as an MCP server
# This means LangGraph nodes can call OpenBB via MCP tools
# rather than direct Python SDK calls

# From OpenBB release notes:
# "[Feature] Add mcp_server to openbb_core api"
```

**Architectural implication for Pantheon:** Instead of building custom data adapter nodes in LangGraph for each data source (Screener.in scraper, NSE API caller, FII/DII fetcher), we may be able to use OpenBB's MCP server as a unified data tool that the LangGraph `data_ingestion_node` calls. One MCP server, all data sources.

### OpenBB for NSE/BSE Data

**Current supported Indian data via OpenBB:**
- yfinance provider: NSE (`.NS`) and BSE (`.BO`) stocks — historical OHLCV
- Financial modeling prep (FMP): Some Indian coverage (requires paid API key)
- Alpha Vantage: Limited NSE coverage (25 calls/day free)

**Current gap:** OpenBB does not have a direct Screener.in or NSE-native provider. For Pantheon's use case, OpenBB is valuable as an OHLCV aggregator (covering the Upstox + yfinance layer) but cannot replace Screener.in for fundamental data.

**Future potential:** OpenBB supports custom provider extensions. Building a Screener.in or NSE provider for OpenBB is a viable open-source contribution that would benefit both Pantheon and the broader community.

### OpenBB Deployment as REST API

```bash
# Start OpenBB as a REST API server
pip install openbb
uvicorn openbb_core.api.rest_api:app --host 0.0.0.0 --port 8000 --reload

# Swagger docs at http://localhost:8000/docs
# All OpenBB endpoints accessible as HTTP REST calls
```

This deployment model means the Pantheon data pipeline could consume OpenBB data via HTTP rather than Python imports — useful if different components of Pantheon run in different processes.

---

## R3.15 — Legal & Scraping Compliance Assessment (Enhanced)

V1 covered the basic legal landscape. The second pass adds important nuance.

### NSE/BSE Data Terms — Updated Position

NSE's official data commercialization strategy (based on the EOD data subscription page found in the second pass) has two tiers:
1. **Free public data:** Bhav copies, FII/DII reports, bulk deals, insider trading disclosures — explicitly made available for public information purposes
2. **Commercial subscription data:** Binary EOD data with full trade-level detail — requires formal subscription

**Updated legal position:** The free bhav copy (CSV), FII/DII reports, and corporate action data are clearly intended for public access. NSE publishes these at predictable URLs specifically to make this data available. Accessing these programmatically for personal research is the intended use.

**What requires formal licensing:**
- Raw tick data (millisecond level)
- Level 2 order book data
- Redistributing any NSE data commercially

### Screener.in — Updated Terms Analysis

Screener.in has a "Screener AI" feature now. Their updated pricing and features suggest they are investing in making the data more accessible. **The platform's business model is selling premium subscriptions, not preventing personal data access.** Reasonable personal-use scraping at 2-second intervals is unlikely to trigger adverse action.

### The Definitive Legal Framework for Pantheon R3 Data Usage

| Data Type | Source | Personal Use | Commercial Use | Method |
|---|---|---|---|---|
| Daily OHLCV | Upstox API | ✅ Licensed | ✅ Licensed | Official API |
| NSE Bhav Copy | NSE Archives | ✅ Intended | ❌ Requires license | Direct download |
| FII/DII Reports | NSE | ✅ Intended | ❌ Requires license | Download/scrape |
| Bulk/Block Deals | NSE/BSE | ✅ Intended | ❌ Requires license | API/download |
| Fundamental data | Screener.in | ✅ Personal use | ❌ Commercial restricted | Scraping (personal) |
| RSS News | ET, MC, BS | ✅ Intended | ⚠️ Aggregation agreements | feedparser |
| Google News RSS | Google | ✅ Intended | ⚠️ ToS check | feedparser |
| NSE Announcements | NSE API | ✅ Intended | ❌ Requires license | API call |
| XBRL Filings | BSE/NSE | ✅ Official | ✅ Official filings | Direct download |
| Google Trends | Google | ✅ Free use | ✅ Free use | pytrends |

---

## R3.16 — Complete Python Library & Package Ecosystem

Updated comprehensive list with all new discoveries from the second pass.

### Core Data Libraries

```
upstox-python-sdk>=2.0.0   # Primary OHLCV — official
yfinance>=1.0.0             # Secondary OHLCV + fundamentals
jugaad_data>=0.24           # NSE-specific OHLCV backup
nseindiaapi                 # NSE bhav copy + corporate actions
nselib                      # NSE index data for regime detection
```

### Technical Analysis

```
pandas-ta>=0.3.14           # 130+ technical indicators
ta>=0.11.0                  # Lighter alternative (40 indicators)
backtrader>=1.9.78          # Backtesting module
vectorbt                    # Fast vectorized backtesting (alternative to backtrader)
```

### News & Sentiment

```
feedparser>=6.0.0           # RSS feed parsing
finnhub-python>=2.4.0       # News API + earnings calendar
pytrends>=4.9.0             # Google Trends data
newspaper3k                 # Full article text extraction from URLs
```

### Fundamental Data (Scraping)

```
requests>=2.31.0            # HTTP client for all scraping
beautifulsoup4>=4.12.0      # HTML parsing (Screener.in, Moneycontrol)
lxml                        # Faster HTML parser (alternative to html.parser)
selenium>=4.0.0             # For JavaScript-rendered pages (if needed)
playwright>=1.40.0          # Modern alternative to Selenium
```

### Data Storage & Processing

```
pandas>=2.0.0               # Core data manipulation
numpy>=1.24.0               # Numerical operations
sqlalchemy>=2.0.0           # Database ORM
psycopg2-binary>=2.9.0      # PostgreSQL driver
redis>=5.0.0                # Caching layer
sqlite3                     # Built-in — for development
```

### Optional: OpenBB Integration

```
openbb>=4.7.1               # Multi-provider financial data platform
openbb-yfinance             # yfinance provider extension
openbb-finviz               # Finviz data (technical screener)
```

### Utility

```
httpx>=0.27.0               # Async HTTP (faster than requests for concurrent calls)
tenacity>=8.2.0             # Retry logic with exponential backoff
schedule>=1.2.0             # Job scheduling
loguru>=0.7.0               # Better logging
python-dotenv>=1.0.0        # Environment variable management
```

---

## R3.17 — NSE Endpoint Reference Map (NEW)

Community-documented NSE internal API endpoints. All require a valid session cookie (one GET to nseindia.com before calling). These are unofficial but stable for personal use.

```python
import requests

# Initialize session (required for all NSE API calls)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com"
})
session.get("https://www.nseindia.com")  # Sets required cookies

NSE_ENDPOINTS = {
    # Market data
    "market_status":     "https://www.nseindia.com/api/marketStatus",
    "all_indices":       "https://www.nseindia.com/api/allIndices",
    "market_turnover":   "https://www.nseindia.com/api/market-turnover",
    
    # Stock data
    "equity_quote":      "https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}",
    "trade_info":        "https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}&section=trade_info",
    "company_info":      "https://www.nseindia.com/api/quote-equity?symbol={SYMBOL}&section=corp_info",
    
    # Historical
    "historical_data":   "https://www.nseindia.com/api/historical/securityArchives?from={FROM}&to={TO}&symbol={SYMBOL}&dataType=priceVolumeDeliverable&series=EQ",
    "index_history":     "https://www.nseindia.com/api/historical/indicesHistory?indexType={INDEX}&from={FROM}&to={TO}",
    
    # Corporate events
    "announcements":     "https://www.nseindia.com/api/corporates-announcements?index=equities&symbol={SYMBOL}",
    "board_meetings":    "https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={FROM}&to_date={TO}",
    "corp_actions":      "https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={SYMBOL}",
    
    # FII/DII
    "fii_dii_today":     "https://www.nseindia.com/api/fiidiiTradeReact",
    "fii_dii_reports":   "https://www.nseindia.com/static/all-reports/historical-equities-fii-fpi-dii-trading-activity",
    
    # Bulk/block deals
    "bulk_deals":        "https://www.nseindia.com/api/snapshot-capital-market-largedeal?type=bulk_deals",
    "block_deals":       "https://www.nseindia.com/api/snapshot-capital-market-largedeal?type=block_deals",
    "short_selling":     "https://www.nseindia.com/api/snapshot-capital-market-largedeal?type=short_sell",
    
    # Insider trading
    "insider_trading":   "https://www.nseindia.com/api/corporates-pit?index=equities&symbol={SYMBOL}",
    
    # Options data
    "option_chain":      "https://www.nseindia.com/api/option-chain-equities?symbol={SYMBOL}",
    "nifty_oi":          "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    
    # Top movers
    "top_gainers":       "https://www.nseindia.com/api/live-analysis-variations?index=gainers",
    "top_losers":        "https://www.nseindia.com/api/live-analysis-variations?index=loosers",
    "most_active_vol":   "https://www.nseindia.com/api/live-analysis-variations?index=volume",
}
```

**Important:** NSE updates these internal endpoints periodically. Always test before production use. Community libraries (NseIndiaApi, nsepython) abstract the session management and endpoint changes, making them more reliable than raw API calls.

---

## R3.18 — Master Data Source Decision Matrix (Enhanced)

For each data type MMCI needs, the primary source, backup, and update strategy.

| Data Type | Primary Source | Backup | Tertiary | Update Freq | Notes |
|---|---|---|---|---|---|
| OHLCV — 60 days daily | Upstox API v3 | yfinance v1.0 | NSE Bhav Copy | Daily post-close | Use Upstox; bhav copy for bulk download |
| OHLCV — intraday | Upstox API v3 | NseIndiaApi | jugaad_data | On demand | Phase 1 needs daily only |
| Nifty 50 (regime) | Upstox API v3 | nselib | NSE Index History API | Daily post-close | 200-day MA computation |
| Delivery volume | NSE Bhav Copy | NseIndiaApi | jugaad_data | Daily post-close | Unique to Indian market context |
| P/E, P/B, ROE, ROCE | Screener.in scrape | yfinance `.info` | Trendlyne scrape | Weekly | Cache 7 days |
| Quarterly results | Screener.in scrape | BSE XBRL | NSE Integrated Filing | On announcement | Integrated Filing = Q1 FY26 onwards |
| Promoter/FII shareholding | Screener.in scrape | NSE company info | BSE XBRL | Quarterly | After SEBI deadline each quarter |
| Analyst consensus estimates | Trendlyne (premium) | Finnhub estimates | Manual | Quarterly updates | Optional enrichment |
| DVM Score | Trendlyne (free) | Compute internally | — | Weekly | Pre-computed quality signal |
| Company news — 48h | RSS feeds (6 sources) | Finnhub company news | Google News RSS | Every 30 min | feedparser pipeline |
| Market-wide news | Pulse by Zerodha | RSS feeds | — | Real-time | During market hours |
| NSE announcements | NSE API | NSE Bhav Copy events | — | Real-time | Board meetings, results dates |
| FII/DII daily flows (cash) | NSE API endpoint | NSE Reports download | Moneycontrol scrape | Daily post-close | Critical macro signal |
| FII F&O positions | NSE API | NSE FII reports | — | Daily post-close | Leading indicator |
| Bulk/block deals | NSE API endpoint | NSE bulk deals page | BSE bulk deals | Daily post-close | Institutional conviction signal |
| Insider trades | NSE API | NSE insider page | BSE disclosures | As filed (daily check) | Smart money signal |
| Earnings calendar | Finnhub (international) | NSE board meetings API | Manual NSE calendar | Weekly | Critical for risk flagging |
| Macro data | RBI DBIE | MOSPI | — | Monthly/quarterly | Context, not daily input |
| Short selling data | NSE API | — | — | Daily post-close | Contrarian indicator |
| Google Trends | pytrends | — | — | Weekly | Optional enrichment |

---

## R3.19 — Pantheon Data Architecture Recommendation (Enhanced)

### Updated StockContext Object — New Fields

Based on all data sources discovered in the second pass, the `StockContext` Pydantic model should be expanded:

```python
class StockContext(BaseModel):
    # Core (unchanged from V1)
    symbol: str
    company_name: str
    sector: str
    current_price: float
    price_history: PriceHistory
    technicals: TechnicalIndicators
    fundamentals: FundamentalData
    news: list[NewsItem]
    market_regime: MarketRegime
    nifty_trend: str
    as_of: datetime

    # NEW from second research pass
    delivery_pct: float | None = None      # % of trades that were delivery (conviction)
    bulk_deals_7d: list[BulkDealItem] = [] # Last 7 days bulk/block deals
    insider_trades_30d: list[InsiderTrade] = [] # Last 30 days insider transactions
    fii_cash_net_7d: float | None = None   # FII net cash market flow, ₹ crores, 7-day
    dii_cash_net_7d: float | None = None   # DII net cash market flow, ₹ crores, 7-day
    fii_futures_long: float | None = None  # FII index futures long % (bullish signal)
    dvm_score: tuple[int,int,int] | None = None  # Durability/Valuation/Momentum (0-100 each)
    earnings_days_away: int | None = None   # Days until next results announcement
    short_sell_pct: float | None = None     # Short selling as % of total volume
```

### Enhanced Data Pipeline Flow

```
MMCI Analysis Run (post-market, 4:30 PM IST)
    │
    ├─→ Upstox API v3:
    │   - 60-day daily OHLCV
    │   - Compute: RSI, MACD, BB, EMA 20/50/200, ATR
    │   - Nifty 50 last 200 days (regime detection)
    │
    ├─→ NSE Bhav Copy + Delivery File:
    │   - Today's delivery volume %
    │   - Bulk/block deals from today
    │
    ├─→ NSE API:
    │   - FII/DII daily cash flows (today + 7-day aggregate)
    │   - FII F&O positions (updated from NSE report)
    │   - Insider trading (last 30 days for symbol)
    │
    ├─→ Screener.in (cached 7 days):
    │   - P/E, P/B, ROE, ROCE, D/E
    │   - Quarterly results (latest)
    │   - Promoter holding % and 4-quarter trend
    │
    ├─→ Trendlyne (optional):
    │   - DVM score
    │   - Analyst consensus estimates
    │
    ├─→ RSS Database (pre-fetched every 30 min):
    │   - Last 48h news matching symbol + sector
    │
    ├─→ Finnhub:
    │   - Days until next earnings announcement
    │   - Any company-specific news not in RSS feeds
    │
    └─→ MMCI Engine:
        - Assemble StockContext (all of the above)
        - 5 model calls (parallel)
        - Consensus scoring → MCISignal
```

---

## R3.20 — Open Items & Carry-forwards

| Item | Details | Priority |
|---|---|---|
| Pulse by Zerodha JSON endpoint | Identify the underlying API endpoint via browser network inspection during development | Medium |
| NSE Integrated Filing endpoint | Map the new Q1 FY26 structured results filing endpoint | Medium |
| OpenBB MCP server for data layer | Evaluate if OpenBB's MCP server can serve as the unified data tool in LangGraph | Architecture phase |
| NSE options chain for implied volatility | High IV = market expects big move = adjust MMCI signal confidence | Future enhancement |
| NSE EOD endpoint stability testing | NSE changes internal URLs periodically — test all endpoints before building reliance on them | Pre-development |
| Trendlyne StratQ API access | Evaluate if the Excel Connect API is developer-friendly enough for Pantheon's data pipeline | Research phase |
| NseIndiaApi bhav copy parsing | Test NseIndiaApi library's ability to parse the binary bhav copy vs. CSV bhav copy | Pre-development |
| Delivery volume data integration | Confirm delivery % data field availability and format from jugaad_data vs. NseIndiaApi | Pre-development |
| FII F&O positions frequency | Verify if NSE's FII F&O positions API updates intraday or only post-market | Pre-development |

---

## Summary — R3 Version 2.0 Complete Picture

| Data Need | Available Free? | Best Source | New Since V1? |
|---|---|---|---|
| Historical OHLCV (25 years) | ✅ Yes | Upstox API | No |
| Daily bhav copy (all NSE stocks) | ✅ Yes | NSE Archives CSV | ✅ New |
| Delivery volume % per stock | ✅ Yes | NSE Delivery Bhav / jugaad_data | ✅ New |
| Bulk/block deals — today + historical | ✅ Yes | NSE API endpoint | ✅ New |
| Insider trading disclosures | ✅ Yes | NSE API + BSE disclosures | ✅ New |
| FII cash flow — daily | ✅ Yes | NSE API | Expanded |
| FII F&O long/short positions | ✅ Yes | NSE reports | ✅ New |
| Short selling data | ✅ Yes | NSE API | ✅ New |
| Fundamental data (P/E, ROE, etc.) | ✅ Scraping | Screener.in | Enhanced |
| DVM quality score | ✅ Free tier | Trendlyne | ✅ New |
| Analyst consensus estimates | ✅ Trendlyne free (limited) | Trendlyne | ✅ New |
| Quarterly results structured | ✅ Yes | BSE XBRL + NSE Integrated Filing | Enhanced |
| Operational metrics (alt data) | Limited free | Tijori Finance | ✅ New |
| News — real-time aggregated | ✅ Yes | Pulse by Zerodha + RSS | Confirmed live |
| News — stock-specific | ✅ Yes | Google News RSS + Finnhub | Confirmed |
| Earnings calendar | ✅ Yes | Finnhub international | Enhanced |
| NSE announcements | ✅ Yes | NSE API endpoint | ✅ New |
| FII/DII flows | ✅ Yes | NSE API | Enhanced |
| Macro data | ✅ Yes | RBI DBIE | No change |
| Multi-provider data layer | ✅ Free | OpenBB Platform | ✅ New |
| Complete NSE endpoint map | ✅ Yes | Community-documented | ✅ New |

---

*End of Document — R3 Version 2.0: Indian Market Data Sources*  
*Data sources identified: 40+*  
*Python libraries catalogued: 20+*  
*New data types discovered in second pass: delivery volume, bulk/block deals, insider trades, FII F&O positions, short selling data, earnings calendar, DVM scores, NSE announcements*  
*NSE API endpoints mapped: 20+*  
*Next: Complete Research Review Session across R1–R6*
