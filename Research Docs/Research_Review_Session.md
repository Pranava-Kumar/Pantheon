# Complete Research Review Session
## Project Pantheon — Cross-Research Synthesis

**Date:** March 21, 2026  
**Documents Reviewed:** R1 v2.0, R2 v1.0, R3 v2.0, R4 v2.0, R5 v2.0, R6 v2.0  
**Total research lines reviewed:** 5,063  
**Purpose:** Identify cross-document conflicts, confirm final architecture decisions, validate assumptions, and produce a green-light assessment for SDLC planning

---

## Section 1 — Cross-Research Conflicts & Tensions

These are cases where two or more research documents say things that are in tension with each other and require explicit resolution before planning begins.

---

### Conflict 1: Mistral Role Inconsistency (R1 vs R5)

**What R1 says:** Mistral downgraded from primary to supplementary/failover. 2 RPM is too restrictive for a primary MMCI role.

**What R5 says:** In several places, R5's description of the MMCI model roster still echoes the original design where Mistral had a primary sentiment role.

**Resolution:** R1 is correct. The updated 5-model roster is:

| Role | Model | Provider | Weight |
|---|---|---|---|
| Primary Reasoning | Gemini 2.5 Pro | Google AI Studio | 25% |
| Real-time Web Intel | Gemini 2.5 Flash | Google AI Studio | 20% |
| Quantitative / Math | Qwen3 32B | Groq | 20% |
| General Reasoning | Llama 3.3 70B or GPT-OSS 120B | Groq | 20% |
| Chain-of-Thought | DeepSeek R1 | DeepSeek Direct | 15% |

Mistral (2 RPM) = failover only. GLM = removed (no free API confirmed). This roster is final.

---

### Conflict 2: OpenRouter's Role (R1 original vs R1 v2)

**The correction:** R1 v2 confirmed OpenRouter RPD is 50/day (not 200). DeepSeek R1 primary source is now the Direct API, not OpenRouter.

**Downstream impact on R5:** R5 cited DeepSeek R1 "via OpenRouter" as the cross-validation model. This is now outdated. DeepSeek Direct has no enforced rate limit and 5M free tokens. OpenRouter becomes a failover only.

**Resolution confirmed:** DeepSeek Direct API is primary. OpenRouter is secondary failover. Add $10 once to unlock 1,000 RPD from OpenRouter.

---

### Conflict 3: 10 OPS Threshold — Phase 3 Registration (R6 v1 vs R6 v2)

**Original R6 stated:** Below 10 OPS, no registration needed.

**R6 v2 corrected:** Below 10 OPS, broker-side registration is NOT required, but exchange-level registration and a generic Algo-ID IS required for any automated order placement.

**Resolution for MMCI:**
- Phase 1-2: No orders placed → No registration of any kind needed
- Phase 3: When automated orders are added → Contact Upstox to register MMCI and obtain generic Algo-ID (simplified path, not full registration)
- The static IP is still the only urgent action before April 1, 2026

---

### Conflict 4: Gemini Data Privacy (R1) vs SEBI Compliance (R6)

**R1 says:** Gemini free tier may use prompts for training. Acceptable for Phase 1-2 (public data).

**R6 says:** For regulated entities using AI (future Phase 4 RA), SEBI's AI/ML framework requires data fiduciary compliance. Client data cannot be shared with third-party AI providers without proper contractual safeguards.

**Resolution:** No conflict for Phases 1-3. For Phase 4 (commercial):
- Migrate Gemini to Tier 1 (pay-per-use, no data training)
- Avoid DeepSeek for any prompt containing client portfolio data
- Ollama local is the safest option for sensitive analysis in Phase 4

---

### Conflict 5: StockContext Size vs Gemini 2.5 Pro RPD

**R3 v2 expanded StockContext** significantly: original 3-4 data types → now 12+ fields including bulk deals, insider trades, FII F&O positions, earnings calendar, short selling data, DVM score.

**R1 says:** Gemini 2.5 Pro has 100 RPD. For a 50-stock watchlist, 50 calls = 50% of daily budget.

**New tension:** A richer StockContext means more tokens per prompt. The 1M token context window handles it easily, but token-per-minute (TPM) limits could become a constraint if all 50 stocks are analyzed in rapid succession.

**Resolution:**
- Gemini's TPM limit is 250,000/minute
- A rich StockContext per stock is approximately 5,000-8,000 tokens
- 50 stocks × 8,000 tokens = 400,000 tokens total
- At 5 RPM with 8,000 tokens each = 40,000 TPM → well within 250,000 TPM
- Spread the 50 stock analyses across the day (not all at once) to stay comfortable within RPD
- No actual conflict, but MMCI should batch analysis in groups of 10 stocks, not all 50 simultaneously

---

### Conflict 6: Upstox MCP Server (R2) vs OpenBB MCP (R3) vs LangGraph MCP (R4)

All three research tasks independently identified the same opportunity: using MCP servers to simplify the data layer rather than writing custom API adapters.

**This is not a conflict — it is cross-validated confirmation.** Three separate research tracks independently arrived at the same conclusion. MCP evaluation (ADR-009) is therefore well-supported.

**The unified picture:**
- Upstox MCP server → portfolio data, live quotes, order placement
- OpenBB MCP server → OHLCV from multiple providers (yfinance, twelve data, etc.)
- NSE/stock-nse-india MCP → All 30 NSE endpoints
- LangGraph MultiServerMCPClient → consumes all three via one interface

If this works, the `data_ingestion_node` requires almost no custom code.

---

### Conflict 7: LangGraph Version in R4 (Corrected)

R4 v1 stated LangGraph 1.1. R4 v2 corrected to 1.0.x. No downstream document was written using "1.1" features specifically. All features referenced (fan-out, reducers, async, checkpointing, caching) are confirmed in LangGraph 1.0. No cascade corrections needed.

---

### Conflict 8: Checkpoint Package Version (R4 Correction)

R4 v1 cited `langgraph-checkpoint-sqlite` at v3.0.3. Actual current version is 4.0.x (breaking schema change).

**Impact:** When the project is initialized, install 4.0.x from day 1. Do not start with 3.x and try to migrate. This affects the `requirements.txt` that will be written during SDLC planning.

---

### Conflict 9: SEBI April 1, 2026 (10 days away) — The Only True Urgency

R6 documents that full SEBI algo trading framework is mandatory for all brokers from April 1, 2026 — ten days from today. Without a static IP registered with Upstox, API access will be suspended.

**Resolution — only action item before development starts:**

1. Contact your Chennai ISP (Jio Fiber, ACT, Airtel) and request a static IP (₹100-400/month)
2. OR set up a DigitalOcean Mumbai droplet (~₹500/month) which gives a permanent static IP
3. Register the IP in Upstox developer console once it's available
4. Enable TOTP 2FA on Upstox if not already done

Everything else is a development concern, not a deadline.

---

## Section 2 — Confirmed Architecture Decisions

These decisions are final. Every one has been cross-validated across multiple research documents. No further debate needed.

### 2.1 — The MMCI Algorithm (Unchanged)

The mathematical core is confirmed and unchanged across all research:

```
S = Σ(w_i × d_i × c_i) / Σ(w_i)    where S ∈ [-1, +1]
D = Var({d_i × c_i})
If D > 0.15  →  HOLD + DISSENT_FLAG
w_i += α × (correct_i - w_i)  [T+5 update]
```

Novelty confirmed (R5): 10 identified gaps in prior literature. Not published elsewhere.

---

### 2.2 — The 5-Model Free-Tier Roster

| Role | Model | Provider | Weight | Key Constraint |
|---|---|---|---|---|
| Primary Reasoning | Gemini 2.5 Pro | Google AI Studio | 25% | 100 RPD — tightest limit |
| Web Intel | Gemini 2.5 Flash | Google AI Studio | 20% | 250 RPD |
| Quantitative | Qwen3 32B | Groq | 20% | 14,400 RPD — most headroom |
| General Reasoning | Llama 3.3 70B | Groq | 20% | 1,000 RPD |
| Chain-of-Thought | DeepSeek R1 | DeepSeek Direct | 15% | None (5M free tokens) |

**Daily budget for 50 stocks:** 250 calls/day. All within limits. Gemini Pro at 50% daily is the binding constraint. Confirmed viable.

---

### 2.3 — LangGraph Architecture (10 ADRs confirmed)

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Static edges (not Send API) for 5-model fan-out | ✅ Final |
| ADR-002 | All model nodes catch all exceptions internally | ✅ Final |
| ADR-003 | TypedDict with total=False for PantheonState | ✅ Final |
| ADR-004 | dissent_check_node with defer=True | ✅ Final |
| ADR-005 | MemorySaver → SqliteSaver 4.0.x → PostgresSaver 4.0.x | ✅ Final |
| ADR-006 | langchain-openai as unified adapter (Groq, Mistral, OpenRouter, DeepSeek) | ✅ Final |
| ADR-007 | LangGraph Long-Term Store for model weight persistence | ✅ Final |
| ADR-008 | Node-level caching, 4-hour TTL, symbol+date+data_hash key | ✅ Final |
| ADR-009 | Evaluate MCP data layer before writing custom adapters | ✅ Final — first task in dev |
| ADR-010 | LangSmith tracing from day 1 (5,000 free traces/month) | ✅ Final |

---

### 2.4 — Data Architecture (4 Layers)

| Layer | Primary Source | Backup |
|---|---|---|
| OHLCV (price data) | Upstox API v3 | yfinance v1.0, NSE Bhav Copy |
| Fundamental data | Screener.in scrape | yfinance .info |
| News (real-time) | RSS feeds (6 sources) + Pulse by Zerodha | Finnhub, Google News RSS |
| Macro / FII / Bulk deals | NSE API endpoints | NSE reports download |

**Expanded StockContext fields confirmed:** delivery %, bulk deals (7-day), insider trades (30-day), FII/DII 7-day net flow, DVM score, earnings_days_away, short_sell %, FII futures positions.

---

### 2.5 — Compliance Architecture

| Phase | Key Requirement | Status |
|---|---|---|
| **Phase 1 (NOW)** | Static IP registered with Upstox before April 1, 2026 | 🔴 URGENT |
| Phase 1 | TOTP 2FA enabled on Upstox | Action needed |
| Phase 1 | Human-in-the-loop: MMCI signals reviewed before manual order | Built into design |
| Phase 1 | No distribution of signals outside immediate family | Personal discipline |
| Phase 3 | Generic Algo-ID registration via Upstox (simplified path) | Pre-Phase 3 task |
| Phase 3 | Exchange-approved server hosting (Indian cloud provider) | Pre-Phase 3 task |
| Phase 4 | RA registration if distributing to paying users | Long-term item |

---

### 2.6 — Developer Toolstack

| Activity | Tool |
|---|---|
| Agentic vibe coding | Cline (90K stars, MCP-native, BYOK) |
| Daily inline completion | Continue.dev + Gemini Flash-Lite |
| Terminal implementation | Aider + DeepSeek V3 |
| Code review | CodeRabbit (if public repo) |
| Architecture chat | Claude.ai (this conversation) |
| Research paper | Overleaf + NotebookLM |

---

## Section 3 — Validated Assumptions

Things the research confirmed that we assumed going in.

| Assumption | Confirmed? | Source |
|---|---|---|
| MMCI architecture has no published precedent | ✅ Yes | R5 — 10 gaps identified |
| Indian LLM equity research is an open field | ✅ Yes | R5 — effectively zero published work |
| Upstox API is free | ✅ Yes | R2 — community confirmed March 11, 2026 |
| 25 years of NSE daily data available | ✅ Yes | R2 |
| All 5 providers can use OpenAI-compatible format | ✅ Yes | R4 — confirmed with correct base_url |
| LangGraph parallel fan-out supports MMCI topology | ✅ Yes | R4 — core documented feature |
| Personal use is explicitly protected by SEBI | ✅ Yes | R6 — safe harbor confirmed |
| Research paper publication requires no SEBI registration | ✅ Yes | R6 — academic activity exempt |
| MMCI novelty claim is defensible against FINSABER critique | ✅ Yes | R5 — regime-aware thresholds directly address it |

---

## Section 4 — Surprises and Non-Obvious Findings

Things the research revealed that were not anticipated when the project was scoped.

**Surprise 1: The Upstox MCP Server exists and is official.** Nobody planned for this. It could eliminate an entire custom data adapter layer. This is the first thing to evaluate in development.

**Surprise 2: Delivery volume data from NSE is free and powerful.** The percentage of traded shares that were actually delivered (vs. intraday speculation) is a conviction signal no existing multi-agent trading system uses. Free, published daily, easily accessible.

**Surprise 3: The SEBI/Chainlink validation.** Chainlink, SWIFT, Euroclear, and six major financial institutions independently ran a multi-LLM consensus experiment at SmartCon 2025 — and their finding ("consensus greatly reduced hallucination risks, disagreements flagged potential errors") is the industry validation of the MMCI architecture. This is unpublished as an academic paper. MMCI can be the first to formally publish and academically validate what the industry already demonstrated.

**Surprise 4: The Groq model roster changed significantly.** Llama 4 Maverick, QwQ-32B, and DeepSeek R1 distill were all deprecated. The new `openai/gpt-oss-120b` is now on Groq — a 120B parameter model running on LPUs. This is potentially the strongest model available free on any provider.

**Surprise 5: LangGraph Long-Term Store is the right home for model weights.** The weight update mechanism was originally designed as a separate PostgreSQL table. LangGraph's own Store API (backed by the same PostgreSQL) is the cleaner, framework-native solution and was not in the original design.

**Surprise 6: FINSABER (KDD 2026) is both a threat and an opportunity.** It is the most comprehensive critique of LLM trading systems ever published. Every system it critiques uses the same design pattern. MMCI explicitly addresses the two core failures FINSABER documents (regime-agnosticism and short backtesting windows). This means MMCI's research paper can position itself as a direct response to the most current critique in the field.

---

## Section 5 — Open Questions Requiring Your Input

Before SDLC planning begins, four questions need answers from you. Everything else is decided.

**Q1 — Development machine RAM**
How much RAM is available on your primary development machine? This determines whether Ollama is a meaningful fallback provider or just theoretical.
- 8 GB → can run 7B models only (limited utility)
- 16 GB → can run Phi-4 14B (decent quality)
- 32 GB → can run Qwen2.5 32B (excellent quality, real MMCI fallback)

**Q2 — Pilot watchlist size**
Should MMCI start with a 10-15 stock pilot or the full 50-stock design?
- 10-15 stocks → faster iteration, lower rate limit consumption, better for early development
- 50 stocks → production-scale from day 1, uses 50% Gemini Pro daily budget
- Recommendation: Start with 10 stocks (1 per sector), expand to 50 after backtesting confirms the system works

**Q3 — GitHub repo visibility**
Public or private?
- Public → CodeRabbit free code review, research paper citations point to the repo, community contributions possible
- Private → proprietary, no external visibility
- Note: The MMCI algorithm will be published in the research paper regardless, so keeping the repo private does not protect the algorithm itself

**Q4 — Paper trading duration**
How long do you want to run MMCI in paper trading mode before live trading?
- 1 month → fast but limited signal validation
- 3 months → covers different market conditions (more robust)
- 6 months → strongest validation, covers at least one earnings cycle
- Recommendation: 3 months minimum — covers bull/bear/sideways regime mix and aligns with R5's backtest methodology requirements

---

## Section 6 — The Green Light Assessment

**Research completeness:** All 6 tasks complete at v2.0 depth. 70+ papers reviewed. 15+ API providers researched. All architecture decisions made and documented. All legal constraints mapped. All data sources identified.

**Unresolved items blocking SDLC start:** None. The four open questions above are scope/preference decisions, not blockers. SDLC planning can begin with reasonable defaults if you prefer.

**The single action before anything else:** Get a static IP and register it with Upstox before April 1, 2026 — 10 days from today. This is compliance, not development. Everything else waits for you to confirm.

---

## Section 7 — Recommended SDLC Starting Point

Once the static IP is handled, here is the logical first document to produce in the SDLC phase:

**SRS (Software Requirements Specification)** — the formal statement of what the system must do, derived from all six research documents. The SRS will be organized as:

1. System Overview (from the MMCI algorithm design)
2. Functional Requirements (from R2, R3, R4 — what data, what processing, what output)
3. Non-Functional Requirements (performance, rate limits from R1, R2; legal constraints from R6)
4. Data Requirements (from R3 v2 — all StockContext fields)
5. Interface Requirements (Upstox API from R2, LLM APIs from R1)
6. Constraint Catalogue (from R6 — SEBI, static IP, personal use boundary)
7. Acceptance Criteria (from R5 — bias-mitigated backtest methodology)

The SRS is the single document everything else (architecture diagrams, API design, database schema, test plans) derives from.

---

## Summary Table — Final Research Verdicts

| Research Task | Key Verdict | Confidence |
|---|---|---|
| R1 — LLM Providers | 5-model free roster confirmed and viable. 250 calls/day well within limits. | ✅ High |
| R2 — Upstox API | Free, reliable, 25yr data. Daily token rotation is manageable. MCP server is the wildcard. | ✅ High |
| R3 — Indian Data | All data needs covered free. 12-field StockContext is richer than any published system. | ✅ High |
| R4 — LangGraph | All MMCI patterns confirmed supported. 10 ADRs finalized. Checkpoint 4.0.x correction issued. | ✅ High |
| R5 — Prior Art | 10 confirmed gaps. Novelty claim is strong and defensible. FINSABER is both threat and opportunity. | ✅ High |
| R6 — SEBI Legal | Personal use is safe. Static IP is the only urgent action (10 days). RA required only if commercial. | ✅ High |

**Verdict: Research phase is complete. Ready to proceed to SDLC planning.**

---

*End of Document — Complete Research Review Session*  
*Next step: Answer the 4 open questions, then begin SRS documentation*
