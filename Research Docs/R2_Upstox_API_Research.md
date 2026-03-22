# R2 — Upstox API Deep Dive
## Project Pantheon Research Documentation

**Version:** 1.0  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Source:** Official Upstox Developer Documentation (live-fetched March 21, 2026)  
**URL:** https://upstox.com/developer/api-documentation/

---

## R2 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R2.1 | Cost & Access Model | ✅ Complete |
| R2.2 | Authentication & Token Management | ✅ Complete |
| R2.3 | Rate Limits — Full Breakdown | ✅ Complete |
| R2.4 | Historical Data API (v3) | ✅ Complete |
| R2.5 | Market Quote & Live Data (REST) | ✅ Complete |
| R2.6 | WebSocket — Real-time Streams | ✅ Complete |
| R2.7 | Portfolio & Order APIs | ✅ Complete |
| R2.8 | Sandbox Environment | ✅ Complete |
| R2.9 | SDK & MCP Integration | ✅ Complete |
| R2.10 | Critical Findings & Architectural Implications | ✅ Complete |
| R2.11 | Open Items & Carry-forwards to R3+ | ✅ Complete |

---

## R2.1 — Cost & Access Model

**Finding: The Upstox Developer API is completely FREE as of March 2026.**

This was a contested point — third-party review sites (Chittorgarh, InvestorGain) still carry old pricing information mentioning subscription charges of ₹499/month. This information is outdated. Confirmed via:

- Official Upstox website tagline: *"API Documentation – Fast Secure Free"*
- Upstox Community post (March 11, 2026): User asked "is api free in upstox or paid?" — Official Upstox community member `DSingh` replied: **"Free."** with link to official API page.
- The Upstox trading API page shows "Valid till 31 March 2026" on a brokerage-free promotion — this refers to brokerage on trades, not the API itself.

**What you already have:** Since you already have a Demat account with Upstox, you can immediately create a Developer App at `account.upstox.com/developer/apps` at zero additional cost.

**What creating an app requires:**
- App name, description
- Redirect URI (can be `http://localhost` for personal use)
- Postback URL (optional for personal use)

**Important note on AMC:** As of February 2025, Upstox charges an Annual Maintenance Charge (AMC) for the Demat account itself. For accounts opened before February 2025, AMC applies from February 2025 onward. This is a Demat account fee, not an API fee. It is separate from API access.

---

## R2.2 — Authentication & Token Management

### Flow Type
Upstox uses **OAuth 2.0 Authorization Code Flow**. This is a standard, well-documented flow.

### The Daily Token Problem ⚠️
This is the single most important finding of R2. **Upstox access tokens expire at the end of each trading day (around 3:45 AM IST the following day).** A new token must be generated every single day.

For a manual trader this is fine — log in once a day. For an automated system like Pantheon, this is a significant architectural challenge.

### Three Token Strategies Available

**Strategy 1 — Manual Token (Development Phase)**
- Go to `account.upstox.com/developer/apps` → click your app → click **Generate**
- Copy the token and paste it into your `.env` file
- Works fine during development and research phases
- Not suitable for production automation

**Strategy 2 — Semi-Automated Token (Recommended for early production)**
- Configure the system to send an authentication request at a specific time (e.g., 8:50 AM IST before market opens)
- Upstox sends a push notification to your mobile
- You approve it with one tap
- The new access token is automatically delivered to your configured **notifier URL**
- The system listens on the notifier URL and stores the token in its database
- This is the recommended approach for solo developers — one tap per day

**Strategy 3 — Extended Token (Read-only, 1 year validity)**
- Valid for **1 year** from generation date, or until the user manually revokes it
- Can only be used for specific read-only APIs (see list below)
- This is the critical opportunity for Pantheon: data fetching needs no daily re-auth

**APIs that accept the Extended Token (Read-only, 1 year validity):**
- Get Positions
- Get Holdings
- Get Order Details
- Get Order History
- Get Order Book

**Extended Token Limitation:** Does NOT work for Historical Data API, Market Quote, or WebSocket. Only portfolio/order read APIs.

### Token Generation Flow

```
User's Browser → GET https://api.upstox.com/v2/login/authorization/dialog
                     ?response_type=code
                     &client_id={API_KEY}
                     &redirect_uri={REDIRECT_URI}
         ↓
     User logs in (OTP or TOTP)
         ↓
     Redirect to {REDIRECT_URI}?code={AUTH_CODE}
         ↓
POST https://api.upstox.com/v2/login/authorization/token
     {code, client_id, client_secret, redirect_uri, grant_type=authorization_code}
         ↓
     Returns: { access_token, extended_token, ... }
```

### Recommended Pantheon Token Architecture

Given the constraints, the recommended approach:

| Use Case | Token Type | Strategy |
|---|---|---|
| Historical data fetch | Standard access token | Semi-automated daily refresh |
| Market quotes (live) | Standard access token | Semi-automated daily refresh |
| Portfolio read (holdings, positions) | Extended token | Set once, valid 1 year |
| Order placement (future feature) | Standard access token | Semi-automated daily refresh |
| Backtesting (no live data needed) | Extended token OR no token | Use cached historical data |

---

## R2.3 — Rate Limits

Source: Official Upstox rate limits page (live-fetched March 21, 2026).

Rate limits are **per-user, per-API**. They are not per-IP or per-app.

### Standard APIs (Historical data, Market Quote, User data, Portfolio)

| Time Window | Request Limit |
|---|---|
| Per second | 50 requests |
| Per minute | 500 requests |
| Per 30 minutes | 2,000 requests |

### Multi-Order APIs (Place, Cancel, Exit Positions — bulk)

| Time Window | Request Limit |
|---|---|
| Per second | 4 requests |
| Per minute | 40 requests |
| Per 30 minutes | 160 requests |

### WebSocket Stream Limits
- **100 instruments per connection** (community-confirmed)
- No published limit on number of simultaneous connections, but best practice is 1 market data connection + 1 portfolio stream connection

### Rate Limit Assessment for Pantheon

For a 50-stock daily watchlist running once per day:

| Operation | API Calls | Fits Within Limits? |
|---|---|---|
| Fetch 60-day daily OHLCV for 50 stocks | 50 calls | ✅ Yes — well within 2000/30min |
| Fetch fundamentals for 50 stocks | 50 calls | ✅ Yes |
| Fetch last 48h market quotes | 50 calls | ✅ Yes |
| Total per analysis run | ~150 calls | ✅ Comfortably within all limits |

The rate limits are **very generous** for our use case. No rate limit management complexity needed for a 50-stock daily watchlist.

---

## R2.4 — Historical Data API (V3)

The Historical Data API V3 is the most important API for Pantheon. It provides the OHLCV data used to compute technical indicators passed to the MMCI models.

### Base URL
```
GET https://api.upstox.com/v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
```

### Data Availability Matrix

| Unit | Interval Options | Available From | Max Per Request |
|---|---|---|---|
| `minutes` | 1 to 300 | January 2022 | 1 month (for 1–15 min intervals) |
| `minutes` | 16 to 300 | January 2022 | 1 quarter |
| `hours` | 1 to 5 | January 2022 | 1 quarter |
| `days` | 1 | January 2000 | 1 decade |
| `weeks` | 1 | January 2000 | No limit |
| `months` | 1 | January 2000 | No limit |

### Response Format (OHLCV + OI)

```json
{
  "status": "success",
  "data": {
    "candles": [
      [
        "2025-01-01T00:00:00+05:30",  // [0] Timestamp (IST)
        53.1,                          // [1] Open
        53.95,                         // [2] High
        51.6,                          // [3] Low
        52.05,                         // [4] Close
        235519861,                     // [5] Volume
        0                              // [6] Open Interest (for derivatives)
      ]
    ]
  }
}
```

### Key Observations

- **Daily data from 2000**: 25 years of daily OHLCV available — excellent for backtesting the MMCI algorithm historically.
- **Minute data from 2022 only**: Limits intraday backtesting to ~4 years. Sufficient for our purposes.
- **Open Interest included**: Useful for derivatives-aware models in future iterations.
- **Timestamps are IST (UTC+5:30)**: All data is in Indian Standard Time. Must handle timezone carefully in the data pipeline.
- **No paid data tier**: The same V3 API with the same historical depth is available to all users for free.

### Instrument Key Format

Instrument keys follow the pattern: `{exchange}_{segment}|{ISIN}`

Examples:
- `NSE_EQ|INE848E01016` — Wipro on NSE Equity segment
- `BSE_EQ|INE848E01016` — Same stock on BSE

The full instruments list is downloadable as a CSV from the Instruments API endpoint. This gives us the complete NSE/BSE instrument universe to build our watchlist from.

### What This Means for Pantheon

For each stock analysis, we need:
- **60 days of daily OHLCV** → 1 API call (daily unit, 60-day range — well within 1 decade limit)
- **Intraday data if needed** → Separate endpoint, same key

A single API call per stock per day is sufficient for all technical indicators we need.

---

## R2.5 — Market Quote & Live Data (REST)

For live/current market prices (during market hours), the Market Quote API provides snapshot data.

### Available Endpoints

| Endpoint | What It Returns |
|---|---|
| Full Market Quote | Bid/ask, LTP, OHLC for the day, volume, OI |
| OHLC Quote | Today's OHLC + LTP only (lighter) |
| LTP Quote | Last Traded Price only (lightest) |

### Key Notes

- All require a valid daily access token
- Rate limit: same as standard APIs (50 req/sec, 500 req/min)
- Responses are snapshots — not streaming. For streaming, use WebSocket.
- LTP endpoint is the most efficient for polling if only price confirmation is needed

### Assessment for Pantheon

MMCI runs **once per day after market close** — so REST market quotes are needed only for current price context in prompts. The live streaming WebSocket is not required for the initial version.

---

## R2.6 — WebSocket — Real-time Streams

Upstox provides two WebSocket streams:

### Market Data Feed V3
- Provides real-time tick-by-tick price data
- Subscribe to specific instruments by instrument key
- **100 instruments per connection** (community-confirmed limit)
- Data includes: LTP, bid/ask, OHLC, volume, OI, depth
- Uses Protocol Buffers (binary) for efficient data transfer — requires protobuf deserialization

### Portfolio Stream Feed
- Real-time order updates, trade confirmations
- Useful for monitoring placed orders
- Essential for the future automated order execution phase

### WebSocket Flow
```
1. Call GET /v3/feed/market-data-feed/authorize → get authorized WebSocket URL
2. Connect to the WebSocket URL
3. Send subscription message with instrument keys and mode
4. Receive streaming data
```

### Assessment for Pantheon

**Phase 1 (current):** WebSocket is NOT needed. MMCI runs end-of-day — REST historical data is sufficient.

**Phase 2 (future — if we want intraday signals):** WebSocket becomes essential. The 100-instrument limit per connection is sufficient for our 50-stock watchlist.

---

## R2.7 — Portfolio & Order APIs

These APIs allow reading and managing the user's actual Upstox portfolio — the real money integration.

### Portfolio Read APIs (usable with Extended Token — 1 year validity)

| API | What It Returns |
|---|---|
| Get Holdings | Long-term equity holdings (stocks owned) |
| Get Positions | Intraday/short-term positions |
| Get Order Book | All orders placed today |
| Get Order History | Historical order data |
| Trade P&L | Realized/unrealized P&L data |

### Order Placement APIs (require daily access token)

| API | What It Does |
|---|---|
| Place Order | Place market/limit/SL/SL-M orders |
| Place Multi Order | Place up to N orders in one call |
| Modify Order | Change price/quantity of pending order |
| Cancel Order | Cancel a pending order |
| GTT Orders | Good-till-triggered conditional orders |

### Order Types Available
- Regular (CNC for delivery, MIS for intraday, CO for cover)
- Market, Limit, Stop-Loss (SL), Stop-Loss Market (SL-M)
- After-Market Orders (AMO)
- Good Till Triggered (GTT) — triggers when price condition is met

### Assessment for Pantheon

**Phase 1 — Research & Signal Generation:** Only read APIs needed (holdings, positions). Use extended token — no daily re-auth required.

**Phase 2 — Paper Trading Simulation:** Use sandbox environment. No real money risk.

**Phase 3 — Live Trading (much later):** GTT orders are the safest starting point — they trigger only when conditions are met and can be cancelled at any time.

---

## R2.8 — Sandbox Environment

Upstox provides a **free sandbox environment** for testing.

### Sandbox Capabilities
- Free, no cost
- Sandbox access tokens valid for **30 days** (vs daily for production)
- Test order placement, modification, cancellation without real money
- End-to-end API testing without time restrictions (not limited to market hours)
- One sandbox app per user account

### Sandbox-Enabled APIs
As of March 2026, only the following APIs have sandbox support:
- Place Order
- Place Order V3
- Place Multi Order
- Modify Order
- Modify Order V3
- Cancel Order
- Cancel Order V3

> **Critical gap:** Historical Data, Market Quote, and WebSocket APIs are **NOT sandbox-enabled**. For testing data ingestion, you need to use the live API (or mock the data manually).

### Assessment for Pantheon

The sandbox is invaluable for testing the **order execution layer** when we reach Phase 3. For Phase 1 and 2, we will mock market data rather than relying on the sandbox.

**Recommendation:** Create both a sandbox app and a live app on your Upstox account now. Use sandbox app credentials during development sprints involving order logic.

---

## R2.9 — SDK & MCP Integration

### Official SDKs Available

| Language | SDK | Install |
|---|---|---|
| Python | `upstox-python-sdk` | `pip install upstox-python-sdk` |
| Node.js | `upstox-js-sdk` | `npm install upstox-js-sdk` |
| Java | Maven package | pom.xml dependency |
| PHP | Composer package | composer.json dependency |

Since Pantheon is Python-based, `upstox-python-sdk` is the primary choice. It wraps all REST endpoints and handles authentication token injection automatically.

### Upstox MCP Integration — Important Discovery

Upstox has an **official MCP (Model Context Protocol) integration**. This is a significant finding.

The documentation states: *"Complete guide to integrate Upstox trading API with AI assistants using Model Context Protocol (MCP). Connect Claude Desktop, ChatGPT, Cursor, and VS Code Copilot for real-time portfolio analysis, automated trading insights, and personalized financial data access."*

This means Upstox exposes an MCP server that AI models (including Claude) can call directly to access portfolio data, market data, and potentially place orders — without writing custom API integration code.

**Implication for Pantheon:** This could drastically simplify the data layer. Instead of building a custom Upstox adapter, we may be able to configure the Upstox MCP server as a LangGraph tool. This needs further investigation in the architecture phase.

**URL to explore:** `https://upstox.com/developer/api-documentation/mcp-integration`

---

## R2.10 — Critical Findings & Architectural Implications

These are the findings from R2 that directly change or constrain the Pantheon system design:

### Finding 1: Daily Token Rotation Is the Biggest Operational Risk
The access token expires every day. For an automated system, this means:
- A daily re-auth flow must be built and maintained
- If the re-auth fails (notification not approved, network issue), the entire system is blind for that day
- **Mitigation:** Use extended token for all read-only data. Use semi-automated daily token for live market quote only. Implement SMS/email alert if daily token refresh fails.

### Finding 2: Daily OHLCV Data From Year 2000 Is Gold for Backtesting
25 years of daily data available for free, per stock, with no limit on how much you can pull. For the MMCI backtesting module (R4), this means we can validate the algorithm against multiple full market cycles — including the 2008 crash, 2020 COVID crash, and 2021-2024 bull market. This is a major advantage for the research paper.

### Finding 3: No Fundamental Data in Upstox API
The Upstox API provides OHLCV price and volume data only. It does **not** provide:
- P/E ratio, P/B ratio, EV/EBITDA
- Revenue, profit, quarterly results
- FII/DII shareholding data
- Management data or news

This means a separate data source is required for fundamental data. This becomes a core finding for **R3 (Indian Market Data Sources)**.

### Finding 4: Upstox MCP Server Could Replace Custom Data Layer
If Upstox's MCP server exposes market data and portfolio data in a format that LangGraph tools can consume, we may not need to build a custom Upstox adapter at all. This needs to be the first thing verified when development begins.

### Finding 5: WebSocket Requires Protocol Buffers
The V3 WebSocket feed uses binary Protocol Buffers format, not plain JSON. This adds a dependency (`protobuf` Python library) and deserialization logic. Not complex, but must be planned for when real-time streaming is needed.

### Finding 6: Sandbox Token Lasts 30 Days
This is very developer-friendly — the sandbox access token is valid for 30 days, meaning you can develop and test all order logic without worrying about daily token rotation. Sandbox should be the default environment until the system is ready for live paper trading.

---

## R2.11 — Open Items & Carry-forwards

| Item | Details | Feeds Into |
|---|---|---|
| Verify Upstox MCP server capabilities | Fetch the MCP integration docs page; confirm what tools are exposed and their data scope | Architecture phase |
| Fundamental data gap | Upstox API provides no fundamentals — need Screener.in, NSE website, or BSE XBRL | R3 (Indian Market Data Sources) |
| AMC charge clarification | Confirm current AMC amount for your account type | Budget planning |
| Instrument key lookup | Download the full instruments CSV from Upstox to confirm symbol format for watchlist stocks | Data pipeline design |
| Extended token generation | Generate this once during API setup; document the steps | API setup checklist |
| Test historical API latency | Measure actual response time for a 60-day daily OHLCV request during market and off-market hours | Performance benchmarking |

---

## Summary — What Upstox API Gives Pantheon for Free

| Need | Available? | Notes |
|---|---|---|
| 25 years of daily OHLCV | ✅ Yes | Via Historical Data V3 API |
| Intraday OHLCV (minute-level) | ✅ Yes (from 2022) | Via Historical Data V3 API |
| Live market price (snapshot) | ✅ Yes | Via Market Quote REST API |
| Real-time streaming | ✅ Yes | Via WebSocket (100 instruments/connection) |
| Portfolio holdings & positions | ✅ Yes | Via Portfolio APIs (Extended Token) |
| Order placement | ✅ Yes | Via Order APIs (daily token required) |
| Fundamental data (P/E, EV/EBITDA) | ❌ No | Need external source (Screener.in) |
| News & sentiment | ❌ No | Need external source (R3) |
| Options chain | ✅ Yes | Available but not needed for Phase 1 |
| Sandbox for safe testing | ✅ Yes | 30-day tokens, order APIs only |
| Python SDK | ✅ Yes | `upstox-python-sdk` on PyPI |
| MCP integration | ✅ Yes (verify) | Official MCP server — investigate |

---

*End of Document — R2: Upstox API Deep Dive*  
*Next: R3 — Indian Market Data Sources (NSE/BSE free data, Screener.in, news sources, SEBI compliance)*
