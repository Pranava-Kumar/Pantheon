# R6 — SEBI Legal & Compliance Research
## Project Pantheon Research Documentation

**Version:** 2.0 — Enhanced Second Pass  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Research Rounds:** 2 (initial pass + comprehensive second pass)  
**Primary Sources Consulted:** SEBI.gov.in circulars, NSE circular NSE/INVG/67858 (full text fetched), Official Gazette notifications, SEBI FAQ circulars, Mondaq, Lexology, Lakshmikumaran & Sridharan, AZB Partners, Burgeon Law, CsKruti.com, ICICIdirect, Kotak Neo, Sahi, AlgoBulls — live-fetched March 21, 2026  
**Disclaimer:** This document is research and analysis, not legal advice. Consult a qualified SEBI-registered legal professional before making compliance decisions.

---

## R6 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R6.1 | SEBI Regulatory Philosophy — 2025-2026 Context | ✅ Enhanced |
| R6.2 | The Complete Algo Trading Circular Timeline | ✅ New — full circular history |
| R6.3 | NSE Circular NSE/INVG/67858 — Full Text Analysis | ✅ New — primary source analysis |
| R6.4 | The 10 OPS Threshold — Complete Specification with Critical Correction | ✅ Corrected + Enhanced |
| R6.5 | White Box vs Black Box — Full Regulatory Specification | ✅ Enhanced |
| R6.6 | Static IP Mandate — Full Technical Specification | ✅ Enhanced |
| R6.7 | Exchange-Approved Server Hosting Requirement | ✅ New — critical finding |
| R6.8 | API Session Security Requirements | ✅ New |
| R6.9 | Investment Adviser Regulations — December 2024 Full Analysis | ✅ Enhanced |
| R6.10 | Research Analyst Regulations — Official Definition + Full Analysis | ✅ Enhanced with Official Gazette text |
| R6.11 | RA Trading Restrictions — Confirmed Application to Black Box Algo Providers | ✅ Enhanced |
| R6.12 | SEBI AI/ML Framework — Tiered Approach Analysis | ✅ Enhanced |
| R6.13 | SEBI Stock Brokers Regulations 2026 — New Broking Framework | ✅ New |
| R6.14 | PMLA/AML/KYC Obligations for SEBI Intermediaries | ✅ New |
| R6.15 | The Tradetron Enforcement Case — Precedent Analysis | ✅ New |
| R6.16 | The Personal Use vs Commercial Use — Full Legal Boundary | ✅ Enhanced |
| R6.17 | Data Licensing Obligations | ✅ Complete |
| R6.18 | Digital Personal Data Protection Act 2023 | ✅ Enhanced |
| R6.19 | Complete Phase-by-Phase Compliance Roadmap | ✅ Enhanced |
| R6.20 | Master Legal Risk Assessment Matrix | ✅ Enhanced |
| R6.21 | Open Items & Critical Actions | ✅ Updated |

---

## R6.1 — SEBI Regulatory Philosophy: 2025–2026 Context

India's capital markets regulator entered 2025-2026 in the most active enforcement phase in its history, driven by hard statistical evidence of retail investor harm.

### The Numbers That Drove Reform

SEBI's own research establishes the problem that every regulation in this document is designed to solve:
- Net losses for individual F&O traders widened **41% to ₹1.05 lakh crore in FY25** — the largest retail loss figure SEBI has ever documented
- **Over 90% of retail F&O traders lose money** consistently across multiple studies
- Algorithmic trading accounted for **97% of foreign institutional investors' profits** in F&O — retail traders had no systematic access to automation
- **120+ stock brokers** received SEBI show-cause notices in October 2024 for association with Tradetron, an unregulated algo platform promising assured returns (see R6.15)

The direction of travel from SEBI's entire 2025-2026 regulatory program is consistent and clear:

> **"Every automated financial activity in India must be traceable, registered, accountable, and auditable. The era of unmonitored algo activity in Indian markets is over."**

### The 2025-2026 Regulatory Wave — Six Major Interventions

| Circular / Regulation | Date | Impact |
|---|---|---|
| SEBI (IA) Second Amendment Regulations | December 16, 2024 | Investment adviser framework modernized |
| SEBI (RA) Third Amendment Regulations | December 16, 2024 | Research analyst scope expanded; black box algo RA requirement |
| SEBI Guidelines for IAs and RAs | January 8, 2025 | Operational guidelines implementing the December amendments |
| **SEBI Circular on Safer Algo Trading** | **February 4, 2025** | **The core algo trading framework for retail investors** |
| SEBI AI/ML Consultation Paper | June 20, 2025 | AI governance framework proposed |
| NSE Implementation Standards (NSE/INVG/67858) | May 5, 2025 | Technical standards for algo trading |
| **SEBI Stock Brokers Regulations, 2026** | **January 7, 2026** | **Complete overhaul of 1992 broking framework** |
| **Full Algo Trading Framework mandatory** | **April 1, 2026** | **10 days from today — affects Pantheon directly** |

---

## R6.2 — The Complete Algo Trading Circular Timeline

Understanding the full history of the February 2025 circular is essential to understanding what is binding now vs. what was proposed.

### Circular Chain of Custody

```
Original consultation: December 13, 2024 (SEBI consultation paper)
    ↓
Core circular issued: February 4, 2025 (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013)
    ↓
NSE initial circular: February 5, 2025 (NSE/INVG/66524) — acknowledgment
    ↓
Implementation deadline extended: July 29, 2025 (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/108)
    (Extended from August 1, 2025 to October 1, 2025 due to broker requests)
    ↓
NSE Implementation Standards: May 5, 2025 (NSE/INVG/67858) — full technical specification
    ↓
NSE consolidated standards: April 29, 2025 (NSE/MSD/67753) — risk management
    ↓
Glide path for non-ready brokers: September 30, 2025 (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/132)
    ↓
Ready brokers go live: October 1, 2025
    ↓
Non-compliant brokers barred from new API clients: January 5, 2026
    ↓
FULL MANDATORY COMPLIANCE: April 1, 2026 (10 days from today)
```

### What "Full Mandatory Compliance" Means from April 1, 2026

All stockbrokers in India, including Upstox, **must**:
- Accept only static IP-authenticated API connections
- Reject any API order without proper authentication
- Maintain 5-year audit trails for all algo orders
- Implement kill switches for rogue algos
- Register all retail algorithms with exchanges and provide Algo-IDs
- Bar clients from API access unless they have provided static IP

---

## R6.3 — NSE Circular NSE/INVG/67858 — Full Text Analysis

This section analyzes the actual text of the NSE implementation circular (fetched directly from NSE archives on March 21, 2026). The full circular is 6 pages and constitutes the binding technical standard for all algo trading by retail investors.

### Section A: API Access Standards — Verbatim Key Provisions

The following are direct regulatory requirements from the circular, not interpretations:

> **"Stockbrokers may provide their clients with API access to their trading systems. To gain access, clients must mandatorily provide the stockbroker with a static IP address(es)."**

> **"The client may give only one static IP address (primary), or provide additional Static IP address (secondary) for the purpose of connectivity redundancy."**

> **"Multiple API keys can be given to the same client (for connecting to different segments, running different algos, etc.). When the client takes the facility of Multiple API keys, then each such API key may be mapped to the same primary/secondary static IPs of that client only or may have separate primary/secondary static IPs for each of the multiple API Keys."**

> **"Clients will have the ability to update their mapped static IP addresses as needed, but not more than once a calendar week."**

> **"A static IP can only be mapped to one client at a time. However, static IPs can be shared between clients provided such clients belong to one family as defined in SEBI circular SEBI/HO/MIRSD/MIRSD-PoD1/P/CIR/2024/169 dated 3 December 2024."**

> **"All API sessions shall be compulsorily logged out every day before the start of the next trading day."**

### Section B: Standards Around APIs Without Registering Algo

> **"If the flow of algo orders from the client to the broker via API is below the defined Threshold Order Per Second (TOPS) i.e. 10 OPS per exchange, the client will not be required to register for algorithmic trading from the broker's system."**

> **"All such algo orders via API which are below the defined Threshold Order Per Second (TOPS), require registration with the Exchange and a generic algo ID shall be provided by the Exchange for such Algos."**

**CRITICAL CLARIFICATION FROM ORIGINAL R6 VERSION:** The first version stated that below 10 OPS, no registration is required. **This is partially incorrect and must be corrected.** The circular explicitly states:
- Below 10 OPS: **broker-side registration NOT required** (lighter path)
- Below 10 OPS: **exchange-level registration IS required** with a generic Algo-ID

This means even for Pantheon's Phase 3 (low-frequency order execution), some form of exchange registration and generic Algo-ID tagging is mandatory. However, this is a simplified/generic registration path, not the full registration required for >10 OPS systems.

### Section I: Operational Specifications — The Server Hosting Requirement

> **"All Retail Algorithms, including those provided by empanelled Algo providers should be hosted [on exchange-approved] servers."**

**This is the most operationally significant finding from the second research pass.** Section I(h) of the NSE circular requires that any retail algorithm executing trades must be hosted on exchange-approved servers. This has major implications for Pantheon Phase 3.

**What "exchange-approved servers" means:**
- Not your personal laptop running a Python script
- Not an arbitrary cloud VPS
- Exchange-specified or exchange-approved infrastructure
- NSE and BSE publish lists of approved hosting providers

**Impact on Pantheon:**
- Phase 1 (signal generation only): Not applicable — no order placement means no "algo" in the regulatory sense
- Phase 3 (automated order execution): Must be hosted on exchange-approved infrastructure

### Section I: Security Requirements — Full Specification

The circular mandates:
- **OAuth-based authentication** (or other mechanism approved by exchange/SEBI)
- **2FA mandatory** for all API access
- **Password protection** with automatic expiry
- **Audit trail** for all orders: minimum 5 years retention
- **No open APIs** — only unique vendor/client-specific API keys with whitelisted static IPs
- **RMS checks** (Risk Management System) mandatory on all API orders

---

## R6.4 — The 10 OPS Threshold — Complete Specification (With Corrections)

### The Three-Tier Structure (Corrected from V1)

The circular creates three distinct tiers, not two:

**Tier 1: Manual Trading (no API)**
- No algo registration required
- No static IP required
- No Algo-ID
- Zero technical compliance burden

**Tier 2: API Below 10 OPS (the Pantheon tier)**
- Static IP: **MANDATORY**
- 2FA: **MANDATORY**
- Session logout daily: **MANDATORY**
- Broker-side registration: **NOT required**
- Exchange generic Algo-ID: **REQUIRED** (simplified registration, not full)
- All algo orders tagged with generic Algo-ID: **REQUIRED**
- Family use restriction: Self + spouse + dependent children + dependent parents only

**Tier 3: API At or Above 10 OPS**
- Everything from Tier 2 PLUS:
- Full algo registration with exchange
- Unique exchange-assigned Algo-ID per strategy
- Complete algorithm documentation submitted to exchange
- Prior exchange approval before going live

### Threshold Nuance — Per Exchange, Not Per Day

The 10 OPS threshold is applied **per exchange, per calendar clock second** at the broker's server. This means:
- 10 OPS on NSE = separate from 10 OPS on BSE
- Trading on both exchanges simultaneously: each has its own 10 OPS limit
- The broker's server clock determines the counting window, not the client

For Pantheon, which would execute at most 1-5 orders per day total: this threshold is entirely irrelevant. Even placing 5 orders simultaneously would be 5 OPS — below the 10 OPS threshold.

### The Personal Use Lock-In

The circular explicitly restricts below-10-OPS personal algo use:

> "If you develop your own algo and get it approved by the exchanges, it can be used only by you and your immediate family members (self, spouse, dependent children/parents)."

This restriction is absolute. A self-developed algorithm using the personal API cannot be:
- Shared with friends or colleagues
- Offered as a service to others
- Monetized in any form without additional compliance

---

## R6.5 — White Box vs Black Box — Full Regulatory Specification

### Official Definitions From Circular

**White Box (Execution Algos):**
Strategies where the logic is fully transparent, disclosed, and interpretable. The user can access the full decision-making rules and underlying methodology.

**Black Box (Non-Disclosed Algos):**
Strategies where the logic is proprietary or hidden from the end user. The user cannot view the internal workings or rationale of how outputs are generated.

### The Key Legal Question: Where Does MMCI Fall?

From the NSE circular and SEBI's FAQ, an expert legal interpretation confirms:

> "While the circular mentions that algo providers will not be regulated by SEBI, providing Black Box Algos will require a Research Analyst License from SEBI."

The MMCI system has two layers:
1. The **outer algorithm** (MMCI's scoring formula, dissent detection, regime classification) — this is mathematically transparent and fully documentable = **White Box**
2. The **inner LLM reasoning** (what each model "thinks" inside the LLM) — this is inherently opaque = **Black Box element**

**Legal classification depends on context:**

| Scenario | Classification | Registration Required? |
|---|---|---|
| MMCI used for personal investing | Not an "algo" under the framework (no automated orders) | No |
| MMCI executes automated orders for self | White Box (MMCI formula is transparent) | Generic Algo-ID (Tier 2) |
| MMCI signals distributed to others, formula disclosed | White Box research service | RA registration |
| MMCI signals distributed to others, LLM methodology hidden | Black Box | RA registration + full disclosure obligations |

**Design decision confirmed:** Publishing the MMCI research paper serves dual purpose:
1. Research publication (academic)
2. White Box disclosure (regulatory) — the paper IS the methodology disclosure

---

## R6.6 — Static IP Mandate — Full Technical Specification

### Sources

- NSE Circular NSE/INVG/67858, May 5, 2025, Section A (fetched directly from NSE)
- SEBI Circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013, February 4, 2025

### Complete Static IP Requirements

| Requirement | Detail |
|---|---|
| Mandatory | Yes — for ALL API-using clients without exception |
| Primary IP | 1 static IP address required |
| Secondary IP | 1 additional static IP allowed (redundancy) |
| Update frequency | Maximum once per calendar week (extraordinary cases: contact broker) |
| Family sharing | Allowed — one IP can serve multiple family members (per SEBI Dec 2024 guidelines) |
| Mapping | One IP can only be mapped to one client at a time (except family sharing) |
| Multiple API keys | Each key can share the client's IPs or have dedicated IPs |
| Effective date | April 1, 2026 — mandatory for all brokers |

### Static IP Options in Chennai

Since you are in Chennai, the following ISPs serve the area:

| ISP | Static IP Option | Estimated Cost | Notes |
|---|---|---|---|
| Jio Fiber | Available on business plans | ₹0–200/month | Confirm availability in your locality |
| ACT Fibernet | Available on higher plans | ₹100–300/month | Strong Chennai coverage |
| BSNL Broadband | Available (legacy service) | ₹100–200/month | Less reliable than private ISPs |
| Airtel Xstream | Business plans offer static IP | ₹200–400/month | Most reliable enterprise option |

### VPS Option (Recommended for Production)

If ISP static IP is unavailable or unreliable, a Virtual Private Server provides:
- Guaranteed static IP
- Always-on operation (no home internet dependency)
- Better uptime for the daily signal pipeline
- Closer to NSE/BSE infrastructure (low latency)

| Provider | Region | Monthly Cost | RAM | Notes |
|---|---|---|---|---|
| DigitalOcean | Mumbai | ~₹500-700 (1GB) | 1 GB | Most developer-friendly |
| AWS EC2 | Mumbai | ~₹600-800 (t3.micro) | 1 GB | Production-grade |
| Hetzner | Germany | ~₹250-350 (CX11) | 2 GB | Cheapest option, latency from India |
| CtrlS / Yotta | Hyderabad | ~₹800-1200 | 2 GB | Indian data center, SEBI-compliant hosting |

**Recommendation:** For Phase 1 (development/research), contact your Chennai ISP first. For Phase 3 (live execution), use an Indian data center provider (CtrlS, Yotta, NxtGen) which likely aligns with the "exchange-approved server" requirement.

### IP Update Limitation — Operational Impact

The 1-update-per-week restriction means:
- If you switch from home internet to VPS, the changeover takes effect with a 1-week delay in updates
- Plan IP transitions in advance
- For extraordinary cases (ISP failure, emergency relocation), contact Upstox directly

---

## R6.7 — Exchange-Approved Server Hosting Requirement (NEW)

This is the most operationally significant new finding from the second research pass.

### The Requirement

NSE Circular NSE/INVG/67858, Section I(h):

> **"All Retail Algorithms, including those provided by empanelled Algo providers should be hosted [on exchange-approved] servers."**

### What "Exchange-Approved Servers" Means in Practice

NSE and BSE maintain approved co-location and hosting facilities. The circular implies that any algorithm executing automated orders should run on approved infrastructure. This is analogous to co-location requirements for institutional HFT, but applied to retail.

### Practical Implications for Pantheon by Phase

**Phase 1 — Signal Generation (No Order Placement):**
This requirement does NOT apply. MMCI is not an "algorithm" in the regulatory sense — it does not place orders. It generates signals that a human reviews before manually placing orders. The server hosting requirement applies to systems that execute trades, not systems that generate research.

**Phase 2 — Paper Trading:**
Does NOT apply. No real orders placed.

**Phase 3 — Automated Order Execution (Future):**
This requirement APPLIES. The Pantheon execution engine would need to be hosted on exchange-approved infrastructure. Options:
- **NSE co-location facility** (Mahape, Navi Mumbai) — institutional grade, expensive
- **Exchange-empanelled hosting providers** — NSE publishes an approved list
- **Indian cloud providers** already on NSE's approved list (CtrlS, NxtGen, Tata Communications)

**What "hosting on exchange-approved servers" does NOT mean:**
- Does not require running from NSE's own data center
- Does not mean colocation with NSE
- Does mean hosting on an exchange-empanelled provider in India

**Key action for Phase 3 planning:** Request NSE's current list of empanelled hosting providers. This list is available to registered members and broker-empanelled clients.

---

## R6.8 — API Session Security Requirements (NEW)

Beyond the static IP, the NSE circular mandates several additional security requirements for all API users.

### Session Management

**Mandatory daily logout:**
> "All API sessions shall be compulsorily logged out every day before the start of the next trading day."

For Pantheon, this means:
- The Upstox access token (which already expires daily) is aligned with this requirement
- The daily token refresh flow (semi-automated push notification) handles this automatically
- Any persistent API connection must be explicitly re-established each morning

**OAuth-based authentication:**
> "Brokers shall be required to have OAuth (Open Authentication) based authentication only or any authentication mechanism allowed/communicated by the Exchange/SEBI from time to time."

Upstox already uses OAuth 2.0 — compliant by default.

**Two-Factor Authentication:**
> "System shall authenticate client access to IBT/STWT/other API through two factor authentication."

Upstox TOTP-based 2FA — compliant by default.

**No open APIs:**
> "Brokers shall be required to put in place system, processes and policies to ensure that open APIs are not permitted, and access is being provided only through a unique vendor client specific API key and static IP whitelisted by the broker."

This means you cannot share your Upstox API key with anyone else. The key is bound to your static IP and your KYC identity. Sharing the key to let someone else access your account violates this requirement.

### Audit Trail Requirements

> "The broker should ensure sound audit trail for all IBT/STWT/Client API/Vendor API orders and trades and be able to provide identification of actual user and user-id for all such orders and trades. The audit trail data should be available for at least 5 years."

This 5-year audit trail obligation falls on Upstox as the broker, not on Pantheon as the client. However, for the MMCI research paper's methodology validation, maintaining your own signal+outcome logs (which the MMCI PostgreSQL database already does) serves as a supplementary audit trail.

---

## R6.9 — Investment Adviser Regulations — Full Analysis

### Governing Regulation

**SEBI (Investment Advisers) Regulations, 2013** — Second Amendment Regulations, December 16, 2024  
**SEBI Guidelines for IAs**, January 8, 2025

### Official Definition of Investment Advice

The December 2024 amendments added an explicit definition of "investment advice":

> Investment advice means advice relating to investing in, purchasing, selling or otherwise dealing in securities or investment products for consideration.

The definition requires ALL THREE elements simultaneously:
1. **Advice** — guidance, recommendation, or opinion
2. **About securities or investment products** — stocks, mutual funds, bonds, etc.
3. **For consideration** — payment, fee, or any form of compensation (including non-cash benefits)

Absence of ANY one element = not investment advice = IA registration not required.

### Is MMCI "Investment Advice"?

**Personal use (no third parties, no consideration):** No. MMCI generates analysis for the developer's own investment decisions. No consideration exchanged. No IA registration.

**Important clarification from December 2024 amendments:**
> "Providing trading calls will not be considered as investment advice unless they are personalized or investor-specific. A person providing such services will have to get registered as a Research Analyst."

This confirms the regulatory architecture: **trading calls → RA regulation, not IA regulation.** MMCI generates BUY/HOLD/SELL signals (trading calls), not personalized investment advice. Even if MMCI is commercialized, the correct registration path is RA, not IA.

### IA Registration Requirements — Full Detail

| Requirement | Specification |
|---|---|
| Qualification | Graduate/PG degree in finance, commerce, economics, banking, capital markets, insurance, actuarial science, or other financial services |
| Certification | NISM-Series-XA (Level 1) + NISM-Series-XB (Level 2) |
| Registration body | IAASB (BSE Administration & Supervision Ltd.) |
| Deposit (0-150 clients) | ₹1 lakh |
| Deposit (150-300 clients) | ₹2 lakhs |
| Deposit (300-1000 clients) | ₹4 lakhs |
| Deposit (1000+ clients) | ₹10 lakhs |
| Part-time IA | Allowed (December 2024); client limit not specified for IA (only for RA) |
| Dual IA+RA registration | Allowed (December 2024 amendment); must maintain strict service separation |

### AI Disclosure Requirement for Registered IAs

From January 8, 2025 SEBI Guidelines:

> "Research Analysts using AI tools must disclose the extent of AI tool usage to clients."

> "The responsibility for investment advisory services lies solely with the IA, irrespective of AI involvement."

If Pantheon is ever used in a commercial IA context (not recommended — RA path is more appropriate), full AI disclosure is mandatory and liability cannot be disclaimed.

---

## R6.10 — Research Analyst Regulations — Official Definition + Full Analysis

### Official Definition of "Research Services" — From Official Gazette

The SEBI (Research Analysts) (Third Amendment) Regulations, 2024, gazetted December 16, 2024, introduces this exact definition (verbatim from Official Gazette No. SEBI/LAD-NRO/GN/2024/220):

> **"(wa) 'research services' means the following services provided by research analyst:**
> **i. preparation or publication of the research report or content of the research report; or**
> **ii. providing or issuing research report or research analysis; or**
> **iii. making 'buy/sell/hold' recommendation; or**
> **iv. giving price target or stop loss target; or**
> **v. offering an opinion concerning public offer; or**
> **vi. recommending model portfolio; or**
> **vii. providing trading calls; or**
> **viii. any other service of similar nature or character, with respect to securities that are listed or proposed to be listed in a stock exchange, whether or not any such person has the job title of 'research analyst' to the clients or other persons or group of persons or general public;"**

**MMCI directly generates items (iii) — "buy/sell/hold recommendation" — and (iv) — "price target."** The critical phrase is: **"to the clients or other persons or group of persons or general public."**

Generating BUY/HOLD/SELL signals for **yourself** is not providing them to "clients or other persons." The legal definition applies when you provide these to others.

### RA Registration Requirements — Updated December 2024

| Requirement | Specification |
|---|---|
| Qualification | Graduate degree in specified fields (experience requirement removed December 2024) |
| Certification | NISM-Series-XV (Research Analyst certification) |
| Registration body | RAASB (BSE Administration & Supervision Ltd. in RA capacity) |
| Deposit (0-150 clients) | ₹1 lakh |
| Deposit (150-300 clients) | ₹2 lakhs |
| Deposit (300-1000 clients) | ₹4 lakhs |
| Deposit (1000+ clients) | ₹10 lakhs |
| Website | Mandatory functional website with SEBI-mandated disclosures |
| Annual audit | Compliance audit within 6 months of financial year end |
| Part-time RA | Allowed; maximum 75 clients |
| Part-time RA client limit exceeded | Must convert to full-time RA |

### Technical Analysis Exemption — Important Nuance

From SEBI's FAQ circular (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/105, July 2025):

> "Technical analyses relating to the demand and supply for a particular sector or index is exempted from the purview of RA Regulations."

**What is NOT exempt:**
- Technical analysis on individual securities (WIPRO.NS, RELIANCE.NS)
- BUY/HOLD/SELL recommendations on individual stocks

**What IS exempt:**
- Sector-level analysis ("The IT sector appears oversold based on RSI")
- Index-level analysis ("Nifty 50 is at a support level")
- Market-wide macro commentary

MMCI's output includes individual stock recommendations → Not exempt from RA regulation when provided to others.

---

## R6.11 — RA Trading Restrictions — Full Confirmation

This is a critical compliance issue for the commercial phase that was raised in V1 but is now confirmed with legal expert interpretation.

### The Restriction (Regulation 16 of RA Regulations)

Research Analysts cannot trade in securities they cover:
- **30 days BEFORE** publishing a research report or recommendation
- **5 days AFTER** publishing a research report or recommendation

### Confirmed Application to Black Box Algo Providers

From expert legal analysis (cskruti.com, December 2024):

**User question:** "Since SEBI has made a law that black box algo providers have to be SEBI RA, I want to ask whether RA compliances and regulations shall also be applicable on black box algo providers or not? For example, will SEBI RA Regulation 16 of trading limitations be applicable on black box algo provider for the securities that black box algo takes trade in?"

**Expert response:** "Yes, in my view, **all the compliance requirements will be applicable to black box algo providers.** [Trading limitations under Regulation 16 apply.]"

### Practical Impact on Pantheon Commercial Phase

If MMCI becomes a registered RA covering 50 NSE stocks:
- 30-day blackout before publishing a signal on WIPRO
- 5-day blackout after publishing a signal on WIPRO
- Since MMCI publishes signals DAILY on all 50 stocks, the developer could be in a perpetual blackout period for their personal portfolio

**Structural solutions:**

**Solution 1 — Separate personal portfolio from MMCI watchlist**
Personal investment portfolio covers stocks NOT in MMCI's commercial watchlist. E.g., MMCI covers Nifty 50; developer personally invests in Nifty Midcap only.

**Solution 2 — Register as non-individual RA (LLP or Pvt Ltd)**
When a company (LLP or Private Limited) registers as RA, the trading restrictions apply to the company, not to individuals personally. The developer retains personal trading freedom in covered securities (with careful separation of personal vs. company activities).

**Solution 3 — White Box classification + methodology disclosure**
If MMCI is fully white-boxed (via research paper), it is registered as a white box algo strategy rather than a "research service." The RA trading restriction applies to research analysts providing research services — a white box execution algo that users can independently verify and replicate may be classified differently.

**Recommended path:** Consult a SEBI-registered legal counsel on this specific question before the commercial phase. The legal interpretation of Regulation 16's application to AI-generated signal systems is an area of active regulatory evolution.

---

## R6.12 — SEBI AI/ML Framework — Tiered Approach Analysis

### Source

**Consultation Paper: "Guidelines for Responsible Usage of AI/ML in Indian Securities Markets"**
Released: June 20, 2025 | Comment deadline: July 11, 2025 | Status: Under finalization as of March 2026

### The Tiered Approach — Critical for Pantheon Classification

The consultation paper explicitly implements a **tiered compliance approach** based on whether the AI system is customer-facing or back-office:

**Tier 1 — High-impact, customer-facing AI deployments:**
Examples: robo-advice, portfolio rebalancing, automated order routing
Requirements: Full model governance + investor disclosure + testing framework + fairness audit + cybersecurity

**Tier 2 — Internal/back-office AI utilities:**
Examples: cybersecurity analytics, regulatory reporting, internal research tools
Requirements: "Light touch" regime — reduced documentation burden

**Where MMCI Falls by Phase:**

| Phase | AI Tier Classification | Compliance Level |
|---|---|---|
| Phase 1 (personal research tool) | Not a regulated entity → outside scope | None |
| Phase 2 (personal paper trading) | Not a regulated entity → outside scope | None |
| Phase 3 (personal live trading) | Personal use → outside scope | None |
| Phase 4 (commercial SaaS) | Tier 1 (customer-facing) | Full compliance required |

### Five Core Principles — Full Detail

**1. Model Governance**
- Designated senior management responsible for AI oversight
- Continuous monitoring and independent audits
- Fallback/contingency plans
- **Input and output data stored for at least 5 years**
- Agreements with third-party AI vendors (our LLM providers)

**2. Investor Protection and Disclosure**
- Full disclosure when AI directly affects clients
- Must include: purpose, limitations, risks, accuracy results, data quality, fees
- Language must be comprehensible to clients (not just technical jargon)
- Investor grievance mechanism required

**3. Testing Framework**
- Segregated testing environment before live deployment
- Shadow testing with real-world data
- Continuous monitoring (AI/ML models can drift over time)

**4. Fairness and Bias**
- Proactive bias detection
- Diverse training data for underlying models
- Staff training on algorithmic discrimination

**5. Data Privacy and Cybersecurity**
- DPDPA compliance for investor data
- Protection against deepfake-generated false financial statements
- Circuit breakers for AI-driven market volatility
- Human oversight of AI systems

### Current Status (March 2026)

The consultation paper's public comment period ended July 11, 2025. As of March 21, 2026, SEBI has NOT yet issued final binding regulations based on this paper. However:
- Multiple legal commentators (Lakshmikumaran & Sridharan, Burgeon Law, Lexology) note it signals the direction of future regulation
- The paper "positions SEBI at the forefront of responsible AI governance"
- Final rules expected in H1 2026 — could be issued any time

**Pantheon action:** Build the 5-year input/output logging requirement into the architecture NOW. The PostgreSQL persistence layer for MMCI signal runs already serves this function. Document it explicitly as an AI governance compliance feature.

---

## R6.13 — SEBI Stock Brokers Regulations, 2026 — New Broking Framework (NEW)

### Background

On January 7, 2026, SEBI replaced the **SEBI (Stock Brokers and Sub-Brokers) Regulations, 1992** — in force for over 33 years — with the comprehensive **SEBI (Stock Brokers) Regulations, 2026** (Notification No. SEBI/LAD-NRO/GN/2026/291).

This is one of the most significant regulatory changes in India's securities market in decades.

### Why This Matters for Pantheon

Upstox is your broker. Its regulatory environment directly affects your API access, compliance obligations, and the standards it enforces on you as a client.

### Key Changes Under 2026 Regulations

**1. Brokers Can Now Undertake Other Financial Activities**
Brokers (like Upstox) can now offer services regulated by RBI, IRDAI, PFRDA, and others — subject to SEBI approval. This enables broker expansion into advisory, insurance, and banking services.

*Impact on Pantheon:* Upstox may expand its service suite, potentially offering data feeds, advisory tools, or RA services directly. Monitor Upstox's product roadmap for services that could complement or compete with MMCI.

**2. Higher Entry Standards and Compliance Requirements**
- 2 years minimum experience required for new broker registration
- At least one designated director resident in India 182+ days per year
- Extended record retention periods
- Mandatory internal surveillance systems
- Mandatory whistleblower policy

*Impact on Pantheon:* Upstox will have stronger internal compliance systems, meaning stricter enforcement of static IP, API key binding, and algo ID requirements on their developer clients.

**3. Suspicious Activity Reporting Mandatory**
Brokers must now have systems to detect, prevent, and report suspicious activity by clients or employees to exchanges without delay.

*Impact on Pantheon:* If MMCI's API usage patterns trigger Upstox's suspicious activity detection (e.g., unusual order patterns, automated trading without static IP), Upstox is now legally obligated to report it. This reinforces the need for compliant setup.

**4. Expanded Material Change Disclosure**
Brokers must report changes in KMP, compliance officers, net worth, and other material changes to SEBI promptly.

*Impact on Pantheon:* Operational stability concern — if Upstox undergoes significant changes, it may affect API availability. Monitor broker regulatory filings.

---

## R6.14 — PMLA/AML/KYC Obligations for SEBI Intermediaries (NEW)

### The PMLA Framework

The **Prevention of Money Laundering Act, 2002 (PMLA)** forms India's core AML framework. SEBI has issued the **SEBI Guidelines on AML Standards/CFT/Obligations of Intermediaries (SEBI AML Guidelines)** that apply to all SEBI-registered intermediaries.

### Key Provision: PMLA Applies to SEBI-Registered Intermediaries

The SEBI AML Guidelines apply to:
- Stock exchanges
- Stockbrokers
- Investment advisers
- Research analysts
- Portfolio managers
- Other SEBI-registered intermediaries

**If Pantheon registers as an RA or IA**, it becomes a SEBI-registered intermediary and PMLA obligations apply in full.

### PMLA Obligations for SEBI Intermediaries (Including RAs/IAs)

| Obligation | Requirement |
|---|---|
| KYC Policy | Board-approved KYC policy: customer acceptance, risk management, customer identification, transaction monitoring |
| Customer Due Diligence (CDD) | Verify identity of all clients before providing services |
| Beneficial Ownership | Identify beneficial owners above 10% threshold (reduced from 25% in 2024) |
| Transaction Monitoring | Monitor all transactions for suspicious patterns |
| Suspicious Transaction Reporting (STR) | Report suspicious transactions to FIU-IND |
| Record Retention | All records maintained for minimum 5 years |
| High-risk Clients | Enhanced Due Diligence (EDD) for Politically Exposed Persons (PEPs) |

### PMLA Relevance to Pantheon by Phase

**Phase 1-3 (personal use):** Not applicable. Personal investors using their own funds are not "reporting entities" under PMLA.

**Phase 4 (commercial RA/IA):** Full PMLA compliance mandatory. Must:
- Implement KYC for every subscriber
- Conduct CDD before onboarding
- File STRs when required
- Maintain 5-year records of all client interactions
- Have a designated Principal Officer for PMLA compliance

**Cost implication:** PMLA compliance for a registered RA requires:
- KYC technology (can use CKYC/CKYCR for central KYC)
- AML monitoring software
- Principal Officer appointment (can be the founder for small RAs)
- Compliance documentation

### The 2024 AML Guideline Tightening

SEBI tightened its AML/CFT guidelines in 2024 with key changes:
- Beneficial ownership threshold reduced from 25% to **10%** for companies
- Group-wide AML/CFT programmes required for financial groups
- Enhanced CDD for high-risk clients and jurisdictions
- Video KYC now accepted for digital onboarding

---

## R6.15 — The Tradetron Enforcement Case — Precedent Analysis (NEW)

### What Happened

In October 2024, SEBI issued **show-cause notices to 120+ stock brokers** for continued association with **Tradetron** — an unregistered algorithm marketplace that had been operating without exchange empanelment.

Tradetron offered:
- Third-party algo strategies on its platform
- API connectivity to broker accounts
- Strategies promising assured returns
- No SEBI registration
- No exchange registration
- No white box/black box classification

### Why This Matters as Precedent

**SEBI's message is unambiguous:** Operating as an algo provider without exchange empanelment is not a technical violation — it is actively enforced with significant penalties to both the platform AND the brokers who hosted it.

The fact that 120+ brokers received notices means SEBI holds brokers responsible for their ecosystem. This has cascading consequences:

1. Brokers are now deeply cautious about who uses their APIs
2. Upstox, having received regulatory scrutiny on this issue, will enforce the new framework strictly
3. Any algo service not following the April 2026 framework risks similar enforcement action

### Application to Pantheon

The Tradetron case validates Pantheon's design philosophy: personal use + white box methodology + research publication = the compliant path. The problematic Tradetron model was: third-party distribution + black box + no registration + assured return promises.

MMCI is on the opposite end of every dimension:
- Personal use (not third-party distribution)
- White box (research paper is the disclosure)
- Academic system (not commercial service)
- No return guarantees

---

## R6.16 — The Personal Use vs Commercial Use — Full Legal Boundary

### The Regulatory Safe Harbor — Verbatim

From the NSE circular FAQ analysis and SEBI circular interpretation:

> "A tech-savvy retail investor who has less than 10 OPS does not need to get registered as an algo provider. Once the threshold is crossed, the individual will be required to register the algo with the trading member, and his family including — self, spouse, dependent children, and dependent parents — can trade using this registered algo."

> "If you develop your own algo and get it approved by the exchanges, it can be used only by you and your immediate family members (self, spouse, dependent children/parents). Commercial use is not permitted."

### "Family" Definition — Official

Per SEBI Circular SEBI/HO/MIRSD/MIRSD-PoD1/P/CIR/2024/169 dated December 3, 2024:

**Family** means: self, spouse, **dependent children, and dependent parents.**

Note: "Dependent" is key. Independent children (adults with their own income) and independent parents are outside this definition unless still financially dependent on the account holder.

### The Complete Boundary Table

| Activity | Legal? | Compliance Required |
|---|---|---|
| Run MMCI on your own Upstox account | ✅ Yes | Static IP + 2FA |
| Review MMCI signals and manually place orders | ✅ Yes | Static IP + 2FA |
| Run MMCI and use auto-execution for your own account | ✅ Yes (below 10 OPS) | Static IP + 2FA + generic Algo-ID registration |
| Run MMCI for parents' Upstox account (dependent) | ✅ Yes | Same static IP can be shared |
| Run MMCI for spouse's Upstox account | ✅ Yes | Same static IP sharing allowed |
| Share MMCI signal report with a friend via WhatsApp | ⚠️ Grey area (no consideration) | Not regulated if free + occasional |
| Create Telegram channel sharing MMCI signals free | ❌ No | RA registration required (public recommendation) |
| Create WhatsApp group charging fees for signals | ❌ No | RA registration required |
| Build paid SaaS for MMCI signals | ❌ No | RA + exchange empanelment + PMLA + DPDPA |
| Publish academic research paper about MMCI | ✅ Yes | No financial regulation applies |
| Post on social media about MMCI methodology | ✅ Yes (academic/educational) | Must include disclaimer: not investment advice |
| Share MMCI backtest results in research paper | ✅ Yes | Standard academic disclosure; SEBI does not regulate academic publications |

---

## R6.17 — Data Licensing Obligations

### NSE/BSE Market Data Terms

**For personal use (non-commercial):**
Upstox's API Terms of Service grant a license to access and use market data for personal trading and investment analysis. This covers:
- Historical OHLCV data for personal backtesting
- Live market quotes for personal investment decisions
- Portfolio data (your own positions/holdings)

**For commercial use:**
- Redistribution of NSE/BSE price data = **NSE Data Vendor License required**
- Pricing (2026 estimate): ₹5–25 lakhs/year depending on scope and number of end users
- Application: Contact NSE at datasales@nse.co.in
- BSE has equivalent licensing: data@bseindia.com

### Screener.in and Other Data Sources

Screener.in ToS explicitly prohibits commercial scraping. For a commercial Phase 4 product:
- Negotiate a data partnership agreement with Screener.in
- Or use a licensed financial data API (Refinitiv, FactSet, Bloomberg — all expensive)
- Or rely on official XBRL filings (free, complex to parse)

### RSS News Feeds

- Personal and research use: Permitted (RSS designed for this)
- Commercial redistribution in a product: Requires agreement with each publisher
- Exception: Analysis/commentary on news (not redistribution) is generally acceptable

---

## R6.18 — Digital Personal Data Protection Act 2023

### Status

DPDPA, 2023 was enacted in August 2023. Rules under the Act were published in 2025. As of March 2026, the Act is operational with compliance expected by registered entities.

**Data Localization:** Rules on cross-border data transfer still being finalized as of March 2026.

### DPDPA and Pantheon

**Phase 1-3:** The DPDPA applies to Data Fiduciaries — entities that determine the purpose and means of processing personal data of others. MMCI in Phase 1-3 processes no personal data of any third party. The DPDPA does not apply.

**Phase 4 (commercial):** Pantheon becomes a Data Fiduciary for subscriber data. Must:
- Provide a clear Privacy Notice before data collection
- Collect only minimum necessary data (data minimization)
- Allow Data Principals (users) to access and delete their data
- Implement security safeguards for stored personal data
- Report breaches to the Data Protection Board of India

### SEBI + DPDPA Intersection

The SEBI AI/ML consultation paper explicitly states that regulated entities using AI must act as "Data Fiduciaries" under DPDPA for investor data. This creates overlapping obligations:
- SEBI AML/KYC: Collect client data for compliance
- DPDPA: Protect that same client data with privacy-by-design

---

## R6.19 — Complete Phase-by-Phase Compliance Roadmap

### Phase 1 — Research, Development & Signal Generation (CURRENT)

**Regulatory status:** Personal investment research tool. No distribution. Zero fees charged. No orders placed automatically.

**Compliance requirements:**

| Requirement | Deadline | Action | Cost |
|---|---|---|---|
| Static IP for Upstox API | **April 1, 2026** | Contact Chennai ISP or set up DigitalOcean Mumbai VPS | ₹100-700/month |
| 2FA for Upstox API | **April 1, 2026** | Enable TOTP (already supported) | ₹0 |
| Register static IP with Upstox developer console | **April 1, 2026** | Login to developer.upstox.com → whitelist IP | ₹0 |
| Below 10 OPS by design | Ongoing | MMCI generates signals; no automated orders in Phase 1 | ₹0 |
| Human-in-the-loop | Ongoing | All orders manually placed by you | ₹0 |
| 5-year signal logging | Build from day 1 | PostgreSQL logs all MMCI runs | ₹0 (DB cost) |
| AI usage in personal research | No regulation | No disclosure required for personal use | ₹0 |

**Total Phase 1 compliance cost: ₹100-700/month for static IP.**

### Phase 2 — Backtesting, Paper Trading, Research Paper

**New compliance requirements beyond Phase 1:** None.

Academic research paper publication does not require SEBI registration. Historical backtesting of NSE data is personal research activity.

### Phase 3 — Live Trading with Automated Execution

**New compliance requirements:**

| Requirement | Action | Notes |
|---|---|---|
| Generic Algo-ID registration | Contact Upstox to register MMCI algo on NSE/BSE | Required for ANY automated order execution |
| Exchange-approved server hosting | Migrate execution engine to Indian cloud provider | Required if hosting outside approved infrastructure |
| Algo documentation | Document MMCI strategy for exchange submission | White box classification simplifies this |
| Enhanced RMS checks | Upstox implements at broker level | No action needed from you |
| Session management | Daily re-auth flow already designed in R2 | No new action |

**Clarification on exchange registration for Phase 3:** Since Pantheon will execute <<10 OPS, it qualifies for the simplified registration path (generic Algo-ID, not full registration). Contact Upstox's API support team for the specific registration process — they guide clients through this as the principal broker.

### Phase 4 — Commercial SaaS

**Full compliance requirements (significant cost and complexity):**

| Requirement | Details | Cost Estimate |
|---|---|---|
| RA registration | NISM-XV certification + RAASB registration | ₹5-50K (exam + application) + ₹1-10L deposit |
| White box classification | MMCI research paper + full documentation | ₹0 (paper already planned) |
| NSE Data Vendor License | For redistributing NSE data to users | ₹5-25L/year |
| PMLA KYC compliance | KYC technology + compliance infrastructure | ₹1-5L setup |
| Website with SEBI disclosures | Functional website with RA registration details | ₹20-50K |
| Annual compliance audit | CA/CS/CMA annual audit | ₹50K-2L/year |
| Exchange empanelment (if >10 OPS) | Apply to NSE/BSE as algo provider | One-time registration |
| DPDPA privacy framework | Legal counsel for privacy notice + data handling | ₹30-50K legal setup |
| RA trading restrictions | Separate personal portfolio from MMCI watchlist | Structural/operational |

**Total Phase 4 compliance cost: ₹20-45 lakhs upfront + ₹7-30 lakhs/year recurring.**

---

## R6.20 — Master Legal Risk Assessment Matrix

| Risk | Phase | Probability | Severity | Mitigation |
|---|---|---|---|---|
| Static IP non-compliance after April 1, 2026 | Phase 1 | 🔴 High if unaddressed | 🟡 Medium (API suspended) | Get static IP before April 1 — URGENT |
| Daily session non-compliance | Phase 1 | 🟡 Medium (if auto-reconnect used) | 🟢 Low | Implement proper daily logout in code |
| Accidental distribution of signals without RA | Phase 1 | 🟡 Medium (social sharing) | 🔴 High (SEBI enforcement) | Personal discipline; add "for personal use only" disclaimers |
| Exceeding 10 OPS in automated trading | Phase 3 | 🟢 Very Low (by design) | 🔴 High | Hard-code rate limiter at ≤1 OPS |
| Missing generic Algo-ID registration | Phase 3 | 🟡 Medium | 🟡 Medium | Contact Upstox for registration process |
| Non-approved server hosting for execution | Phase 3 | 🟡 Medium | 🟡 Medium | Use Indian cloud provider (CtrlS, NxtGen) |
| RA trading restriction violation | Phase 4 | 🟡 Medium | 🔴 High | Separate personal portfolio from MMCI watchlist |
| Commercial distribution without RA registration | Phase 4 | 🟢 Low if planned | 🔴 High | Register as RA before any paid distribution |
| NSE data redistribution without license | Phase 4 | 🟢 Low | 🔴 High | Obtain NSE data vendor license |
| PMLA non-compliance (no KYC for subscribers) | Phase 4 | 🟡 Medium | 🟡 Medium | Implement KYC from first paid subscriber |
| DPDPA data handling violation | Phase 4 | 🟡 Medium | 🟡 Medium | Privacy notice + consent framework from launch |
| AI governance non-compliance (when rules finalized) | Phase 4 | 🟡 Medium | 🟡 Medium | Build 5-year logging now; monitor SEBI for final rules |
| Academic paper publication triggering RA registration | Phase 2 | 🟢 Very Low | 🟢 Low | Academic publication ≠ financial service |
| Tradetron-type enforcement action | All | 🟢 Very Low | 🔴 High | MMCI is personal use + white box — opposite profile |

---

## R6.21 — Open Items & Critical Actions

### URGENT — Before April 1, 2026 (10 days)

| Action | Owner | Deadline |
|---|---|---|
| Get static IP address (ISP or VPS) | You | Before April 1, 2026 |
| Login to developer.upstox.com, locate IP whitelisting feature | You | Before April 1, 2026 |
| Enable TOTP 2FA on Upstox app if not already done | You | Before April 1, 2026 |
| Confirm whether Upstox has already rolled out static IP registration | You | Before April 1, 2026 |

### MEDIUM PRIORITY — Before Development Begins

| Action | Owner | When |
|---|---|---|
| Research Upstox's generic Algo-ID registration process for Phase 3 | You | Before Phase 3 planning |
| Confirm NSE's list of exchange-approved hosting providers | You | Before Phase 3 infrastructure design |
| Monitor SEBI AI/ML framework final rules (expected H1 2026) | Ongoing | Monthly check |
| Draft disclaimer language for any public communication about MMCI | You | Before any social media/conference mention |

### LOWER PRIORITY — Phase 4 Planning

| Action | Owner | When |
|---|---|---|
| Consult SEBI-registered legal counsel on RA trading restriction scope for AI-generated signals | Legal counsel | 3 months before Phase 4 |
| Contact NSE for data vendor license pricing (datasales@nse.co.in) | You | Phase 4 planning stage |
| Consider LLP/Pvt Ltd entity for commercial phase (avoids personal RA trading restrictions) | Legal counsel | Phase 4 planning |
| NISM-XV exam registration | You | 6 months before commercial launch |

---

## Summary — R6 Version 2.0 Complete Picture

| Question | Answer |
|---|---|
| Is building MMCI for personal use legal? | ✅ Completely legal. No registration needed. |
| What must be done before April 1, 2026? | Get a static IP. That is the ONLY urgent action. |
| Does MMCI need exchange algo registration? | Phase 1-2: No (no orders placed). Phase 3: Yes — generic Algo-ID required (simplified path). |
| Does MMCI need to be hosted on exchange-approved servers? | Phase 1-2: No. Phase 3: Likely yes. Indian cloud providers (CtrlS, NxtGen) are the practical solution. |
| Is the research paper publication regulated? | ❌ No. Academic publication is not a financial service. |
| Do RA trading restrictions apply to black box algo providers? | ✅ Yes — confirmed by expert legal analysis. Design around this for Phase 4. |
| What is the "research services" definition? | Explicitly includes "buy/sell/hold recommendation" and "trading calls." Applies when provided TO others for consideration, not for personal use. |
| When is PMLA compliance required? | Only when Pantheon becomes a SEBI-registered intermediary (IA or RA). |
| Is SEBI's AI/ML framework binding today? | ❌ Not yet — consultation paper status. Final rules expected H1 2026. |
| What is the most important new finding from the second pass? | The generic Algo-ID requirement for below-10-OPS execution (Section B of NSE circular), and the exchange-approved server hosting requirement for algo execution (Section I of NSE circular). V1 was incorrect on the first point. |

---

*End of Document — R6 Version 2.0: SEBI Legal & Compliance Research*  
*All 6 Research Tasks (R1–R6) are now complete at version 2.0 depth.*  
*Next: Complete Research Review Session — consolidate all findings across R1–R6, identify cross-research conflicts, confirm final architecture decisions, then proceed to SDLC documentation.*
