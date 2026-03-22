# R1 — Free AI Tool Ecosystem & LLM API Access Research
## Project Pantheon Research Documentation

**Version:** 2.0 — Enhanced Second Pass  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Research Rounds:** 2 (initial pass + comprehensive second pass including AI developer tools)  
**Sources:** Google AI Dev docs (March 16–18, 2026), Groq official deprecation log (console.groq.com), OpenRouter official pricing page (live March 21, 2026), Awesome Agents guide (Feb 26, 2026), TLDL LLM pricing (March 17–18, 2026), cheahjs/free-llm-api-resources (live), SambaNova dev docs, DeepSeek API docs — live-fetched March 21, 2026

---

## KEY CORRECTIONS FROM V1

Before anything else, four corrections from V1 that directly affect MMCI architecture:

| Item | V1 (Wrong) | V2 (Correct) |
|---|---|---|
| OpenRouter RPD | "200/day per model" | **50/day total** (free) OR **1,000/day** ($10+ balance) |
| Gemini 2.0 Flash | "Available" | **Retired March 3, 2026** |
| Mistral RPM | Not clearly stated | **2 RPM** — extremely restrictive |
| Groq Llama 4 Maverick | "Available" | **Deprecated Feb 20, 2026** → GPT-OSS 120B |

---

## R1.1 — Free Research & Documentation Tools

**Research:** NotebookLM (free, no limits), Elicit, Consensus, Semantic Scholar, SciSpace, Perplexity AI  
**Docs:** Obsidian (free desktop), Notion (free personal), GitHub (free), Zotero (free), Overleaf (free solo)

---

## R1.2 — Gemini API Free Tier

### Confirmed Limits (March 2026, triple-verified)

| Model | RPM | RPD | TPM | Context |
|---|---|---|---|---|
| Gemini 2.5 Pro | 5 | 100 | 250,000 | 1M tokens |
| Gemini 2.5 Flash | 10 | 250 | 250,000 | 1M tokens |
| Gemini 2.5 Flash-Lite | 15 | 1,000 | 250,000 | 1M tokens |

All on the free tier. No credit card required. Limits are per Google Cloud project (not per key). RPD resets midnight Pacific = 1:30 PM IST.

Google's PM confirmed the December 2025 quota cuts were permanent — free limits "were originally only supposed to be available for a single weekend." The 80% reduction on Pro (from ~500 to 100 RPD) is the new baseline.

**Two additional preview models free:** Gemini 3 Flash and Gemini 3.1 Flash-Lite — more restrictive limits. Gemini 3.x Pro is paid-only preview.

**Data privacy warning:** On the free tier, prompts may be used to improve Google products. Acceptable for Phase 1-2 (public market data). Upgrade to Tier 1 (pay-per-use, billing enabled) before passing portfolio data. Tier 1 = 1,000 RPD, 150 RPM, no data sharing.

**Unique MMCI value:** Native Google Search grounding — the only free provider with built-in web search. Irreplaceable for the Real-time Intel role.

---

## R1.3 — Groq Free Tier

### Corrections: Model Deprecations

- Llama 4 Maverick deprecated Feb 20, 2026 → replaced by `openai/gpt-oss-120b`
- `mistral-saba-24b` deprecated → replaced by `qwen/qwen3-32b`
- `qwen-qwq-32b` deprecated → replaced by `qwen/qwen3-32b`
- `deepseek-r1-distill-llama-70b` deprecated Sep 2025 → `llama-3.3-70b-versatile` or `gpt-oss-120b`

### Current Active Free Models (March 2026)

| Model | RPM | RPD | MMCI Role |
|---|---|---|---|
| `qwen/qwen3-32b` | **60** | **14,400** | Primary quantitative — highest free RPD of any capable model globally |
| `llama-3.3-70b-versatile` | 30 | 1,000 | General reasoning + fundamentals |
| `openai/gpt-oss-120b` | 30 | ~1,000 | New flagship — 120B parameters on Groq LPUs |
| `kimi-k2` | 30 | 1,000 | Long-context analysis |
| `llama-3.1-8b-instant` | 30 | 14,400 | Fast screening |

Rate limits per organization, not per key. Creating multiple accounts to bypass limits violates ToS.

Groq speed: 300–800 tokens/second. MMCI parallel calls complete in under 2 seconds per model.

---

## R1.4 — OpenRouter Free Tier

### CRITICAL CORRECTION

**V1 stated 200 RPD. Actual limit is 50 RPD (no balance).**

On April 9, 2025, OpenRouter reduced the daily free model call limit from 200 to 50. Users with $10+ balance get 1,000 RPD.

| Status | RPM | RPD |
|---|---|---|
| No balance | 20 | **50 total** across all free models |
| $10+ credit balance | 20 | **1,000 total** |

**Strategic action:** Add $10 to OpenRouter once during setup. This unlocks 1,000 RPD and makes OpenRouter useful as a supplementary provider.

**Failed requests still count toward quota.** Build proper error handling.

### Free Models Available (`:free` suffix)

DeepSeek R1, DeepSeek V3, Qwen3 235B (largest free model), Qwen 2.5 72B, Llama 3.3 70B, Gemini 2.5 Flash, Phi-4, Mistral Small 3.1.

### openrouter/free Auto-Router

```python
from langchain_openai import ChatOpenAI
# Auto-selects from all available free models
free_router = ChatOpenAI(
    model="openrouter/free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)
```

Use as the failover of last resort — when all specific providers are rate-limited.

---

## R1.5 — Mistral AI Free Tier

**Official limit confirmed: 2 RPM** on the free "Experiment" tier.

1 request every 30 seconds. 1 billion tokens/month. All Mistral models included (Small 3.1, Large, Codestral, Pixtral, Embed, OCR). No credit card required.

The 2 RPM limit makes Mistral inappropriate for real-time or high-frequency use. For MMCI's once-per-day analysis, it is workable with appropriate spacing. Downgraded from primary to supplementary role.

---

## R1.6 — NEW: GitHub Models

GitHub Models gives free API access to frontier models including GPT-4.1, o3, xAI Grok-3, DeepSeek-R1, Llama 3.1 405B, and more. Available to all GitHub users — no payment.

| Tier | Models | RPM | RPD | Context Limit |
|---|---|---|---|---|
| High | GPT-4.1, o3, GPT-5 | 10 | 50 | **8K input / 4K output** |
| Low | Phi-4, Llama 4 Scout | 15 | 150 | 8K input / 4K output |

**Context limitation is critical:** 8K input tokens maximum. Full StockContext exceeds this. Must compress prompts before sending.

**MMCI role:** Validation only. Send compressed 2,000-token signal summaries to o3 for chain-of-thought cross-validation. The 50 RPD is sufficient for validating the most uncertain signals daily.

**Access:** github.com/marketplace/models — existing GitHub account.

---

## R1.7 — NEW: SambaNova

Persistent free tier — no expiry on access. $5 bonus credit on signup (expires 30 days), then free RPM-limited access continues indefinitely.

**Official free tier rate limits:**

| Model | Free RPM |
|---|---|
| Llama 3.1 405B | 10 |
| Llama 3.3 70B | 20 |
| Qwen 2.5 72B | 20 |
| QwQ 32B Preview | 10 |

No published RPD limit. Speed: 132 tokens/sec on 405B. Fastest large model inference available free.

**MMCI role:** High-quality Groq backup. Zero code changes — same Llama/Qwen models, OpenAI-compatible API.

**Access:** cloud.sambanova.ai — no credit card.

---

## R1.8 — NEW: DeepSeek Direct API

**DeepSeek API does NOT constrain user's rate limit. We will try our best to serve every request.**

| Feature | Value |
|---|---|
| Free tokens on signup | **5 million** (valid 30 days) |
| Rate limit | **None enforced** |
| DeepSeek V3 price after free | $0.14/M input tokens |
| DeepSeek R1 price after free | $0.55/M input tokens |
| Credit card required | No |
| Data residency | China |

5M free tokens = ~5,000 full MMCI analysis calls. Covers entire development + testing phase.

After free tokens: $0.55/M tokens for R1 means 1,000 MMCI calls/month = ~$0.55/month. Quasi-free.

**MMCI role:** DeepSeek R1 as the chain-of-thought validation model. No rate limit = always completes in the parallel call. Best free chain-of-thought provider available.

**Data privacy note:** Chinese data servers. Acceptable for public market data analysis. Avoid for personal portfolio data.

**Access:** platform.deepseek.com — email signup.

---

## R1.9 — NEW: Cerebras

Custom wafer-scale hardware. Ultra-fast inference.

| Feature | Value |
|---|---|
| RPM | 30 |
| Daily token limit | 1 million tokens |
| Speed | Ultra-fast (wafer-scale) |
| API format | OpenAI-compatible |
| Credit card | Not required |

**Models:** Llama 3.3 70B, Qwen3 32B, Qwen3 235B, GPT-OSS 120B.

**MMCI role:** Primary Groq failover. Same models, same API format, zero code changes needed.

**Access:** cloud.cerebras.ai — no waitlist.

---

## R1.10 — NEW: Cloudflare Workers AI & Cohere

### Cloudflare Workers AI

10,000 neurons/day free. Uniquely hosts GLM-4.7-Flash (not free elsewhere) and Qwen3 30B. Best for edge deployment of Pantheon dashboard rather than MMCI core models.

### Cohere

20 RPM, **1,000 requests/month total** (~33/day). Too restrictive for MMCI signal generation. Use only for Embed 4 (embeddings) and Rerank 3.5 in Phase 3+ semantic tool selection.

---

## R1.11 — NEW: Fireworks AI & Vercel AI Gateway

**Fireworks AI:** 10 RPM free (no card), 6,000 RPM with payment method linked. Llama 3.1 405B, DeepSeek R1.

**Vercel AI Gateway:** $5/month free credit. Covers Claude, GPT-5, Gemini, DeepSeek via one gateway. Requires credit card. The only free path to Claude API access without paying Anthropic directly.

---

## R1.12 — Ollama Local Models

Zero cost. Zero rate limits. Full data privacy. OpenAI-compatible at `http://localhost:11434/v1`.

| Model | RAM | Quality | Best For |
|---|---|---|---|
| Qwen2.5 7B | 8 GB | Good | Dev testing |
| Phi-4 14B | 16 GB | Very Good | Balanced |
| Qwen2.5 32B Q4 | 20 GB | Excellent | Primary local |
| Llama 3.3 70B Q4 | 40 GB | Near-frontier | Highest local quality |

**Action required:** Determine available RAM on your machine.

---

## R1.13 — Free Chat Platforms as Supplementary Tools

| Platform | Model | Key Use for Pantheon |
|---|---|---|
| Claude.ai (free) | Claude Sonnet 4.6 | This conversation — architecture, planning |
| DeepSeek Chat | DeepSeek V3.2 | Generous limits — quantitative reasoning |
| ChatGPT | GPT-4o (free tier) | Cross-validation |
| Gemini Advanced | Gemini 2.5 Pro | Web-grounded analysis |
| Qwen Chat | Qwen Max | APAC market context |
| GLM Chat | GLM-5 | News sentiment, agent mode |
| Perplexity | Multiple + web | Real-time cited research |

---

## R1.14 — NEW: AI Coding & Developer Productivity Tools

These are tools that help YOU build Pantheon — not MMCI's model providers.

### R1.14.1 GitHub Copilot Free

**Free tier:** 2,000 code completions/month + 50 chat messages/month. Works in VS Code, JetBrains, Neovim. No credit card.

Best starting point — zero friction. 50 chat messages/month runs out in heavy sessions; use Claude.ai for architecture discussions.

**Access:** github.com/features/copilot

---

### R1.14.2 Continue.dev — Best Free Alternative (BYOK, Unlimited)

Open-source AI coding assistant for VS Code/JetBrains. Connect to your free Gemini API key → zero additional cost. Autocomplete + chat + code refactoring.

```json
{
  "models": [{"title": "Gemini 2.5 Flash", "provider": "google",
    "model": "gemini-2.5-flash", "apiKey": "YOUR_KEY"}],
  "tabAutocompleteModel": {"title": "Flash-Lite", "provider": "google",
    "model": "gemini-2.5-flash-lite", "apiKey": "YOUR_KEY"}
}
```

Flash-Lite for fast autocomplete (minimal RPD usage). Flash for chat. This setup costs ₹0/month.

**Access:** continue.dev — VS Code marketplace.

---

### R1.14.3 Cline — Agentic Coding (90K+ Stars, BYOK)

Autonomous AI coding agent for VS Code. Can plan, write multi-file code, run terminal commands, use browser, and extend via MCP.

**Why Cline is the premier vibe coding tool for Pantheon:**
- Describe what you want → Cline writes the LangGraph node, writes the test, runs it, sees errors, fixes them
- Native MCP support — can call Upstox MCP and OpenBB MCP during development
- Works with Gemini, DeepSeek, Groq, Ollama — all your free keys
- Full filesystem access — reads/writes any Pantheon file

**Access:** cline.bot — VS Code extension. BYOK.

---

### R1.14.4 Aider — Terminal Pair Programmer (Open Source, Auto-Git)

Implements features across multiple files and creates automatic git commits with meaningful messages.

```bash
pip install aider-chat
aider --model deepseek/deepseek-chat --api-key deepseek=YOUR_KEY pantheon/mmci/scoring.py
```
Cost per feature implementation: ~₹0.01 using DeepSeek V3.

**Access:** aider.chat — pip install.

---

### R1.14.5 OpenCode — Terminal-Native TUI (95K+ Stars, BYOK)

Open-source AI coding with polished terminal UI. Deep LSP integration. Works with Groq free tier for ultra-fast terminal responses.

---

### R1.14.6 Gemini Code Assist — Free Google IDE Integration

Google's AI coding assistant for VS Code/JetBrains. Free individual tier. Uses Gemini models. Best for Google Cloud workflows.

---

### R1.14.7 Windsurf — AI-Native IDE with BYOK Mode

Codeium's AI-native IDE. **Free with BYOK** — link your Gemini API key → unlimited Cascade features at zero cost. Full VS Code-compatible experience.

---

### R1.14.8 CodeRabbit — AI Code Review (Free for Open Source)

Automated AI code review on every pull request. Free for public GitHub repositories. If Pantheon is public (beneficial for research paper reproducibility), CodeRabbit catches bugs in MMCI nodes automatically.

**Access:** coderabbit.ai

---

### Recommended Developer Toolstack for Pantheon

| Task | Tool | Cost |
|---|---|---|
| Daily inline completion | Continue.dev + Gemini Flash-Lite | ₹0 |
| Complex multi-file agentic coding | Cline + Gemini Flash | ₹0 |
| Terminal-based feature implementation | Aider + DeepSeek V3 | ~₹0.01/session |
| Model playground testing | GitHub Models web UI | ₹0 |
| Automated code review | CodeRabbit (public repo) | ₹0 |
| Architecture decisions | Claude.ai (this conversation) | ₹0 free tier |
| Research paper writing | Overleaf + NotebookLM | ₹0 |

**Total developer tooling cost: ₹0/month** using BYOK tools with free API keys.

---

## R1.15 — NEW: Data Privacy by Provider

| Provider | Free Tier Data Usage | Phase 1-2 OK? |
|---|---|---|
| Gemini (Google) | May train on prompts | ✅ Public data OK; avoid portfolio data |
| Groq | No training | ✅ Yes |
| Mistral | No training | ✅ Yes |
| DeepSeek | Chinese servers | ✅ Public data OK; avoid portfolio data |
| SambaNova | No training | ✅ Yes |
| GitHub Models | Microsoft policy | ✅ Yes |
| Cerebras | No training | ✅ Yes |
| Ollama (local) | Never leaves device | ✅ Fully private |

---

## R1.16 — NEW: Rate Limit Budget Calculation

**50-stock daily watchlist — all within free limits:**

| Role | Provider | Calls/Day | Limit | Usage |
|---|---|---|---|---|
| Primary reasoning | Gemini 2.5 Pro | 50 | 100 RPD | 50% |
| Web intel | Gemini 2.5 Flash | 50 | 250 RPD | 20% |
| Quantitative | Groq Qwen3 32B | 50 | 14,400 RPD | 0.3% |
| General reasoning | Groq Llama 3.3 70B | 50 | 1,000 RPD | 5% |
| Chain-of-thought | DeepSeek R1 (direct) | 50 | None | N/A |
| **TOTAL** | | **250** | | All within limits |

Gemini 2.5 Pro at 50% is the tightest constraint. All other providers have substantial headroom.

---

## R1.17 — Consolidated Provider Comparison Matrix

| Provider | Key Free Models | RPM | RPD | Speed | Web Search | Credit Card |
|---|---|---|---|---|---|---|
| Google AI Studio | Gemini 2.5 Pro/Flash/Flash-Lite | 5–15 | 100–1,000 | Medium | ✅ Native | No |
| Groq | Qwen3 32B, Llama 3.3 70B, GPT-OSS 120B | 30–60 | 1,000–14,400 | Ultra-fast | No | No |
| OpenRouter | DeepSeek R1, Qwen3 235B | 20 | **50**(free)/**1,000**($10+) | Medium | No | No |
| Mistral AI | Small 3.1, Large | **2 RPM** | ~1B tokens/mo | Fast | No | No |
| GitHub Models | GPT-4.1, o3, DeepSeek-R1 | 10–15 | 50–150 | Medium | No | No |
| SambaNova | Llama 3.1 405B, Llama 3.3 70B | 10–30 | No RPD limit | Fast | No | No |
| DeepSeek Direct | V3.2, R1 | **None** | **None** | Medium | No | No |
| Cerebras | Llama 3.3 70B, Qwen3 32B/235B | 30 | 1M tokens/day | Ultra-fast | No | No |
| Ollama | Any open-source | Unlimited | Unlimited | HW-dependent | No | N/A |

---

## R1.18 — Revised MMCI Model Role Assignments (March 2026)

| Role | Model | Provider | Init Weight | Change from V1 |
|---|---|---|---|---|
| Primary Reasoning + Macro | Gemini 2.5 Pro | Google AI Studio | 25% | Unchanged |
| Real-time Web Intel | Gemini 2.5 Flash | Google AI Studio | 20% | 2.0 Flash retired; 2.5 Flash confirmed |
| Quantitative / Math | Qwen3 32B | Groq | 20% | QwQ deprecated → Qwen3 32B |
| General Reasoning | Llama 3.3 70B OR GPT-OSS 120B | Groq | 20% | GPT-OSS 120B new option |
| Chain-of-Thought | DeepSeek R1 | **DeepSeek Direct** | 15% | Moved from OpenRouter (50 RPD limit) → Direct API (no limit) |

Mistral downgraded from primary to failover (2 RPM too restrictive for primary role). GLM removed (no free API).

---

## R1.19 — Failover Strategy

| Primary | Failover 1 | Failover 2 | Last Resort |
|---|---|---|---|
| Gemini 2.5 Pro | Gemini 2.5 Flash | Gemini 2.5 Flash-Lite | SambaNova Llama 3.3 70B |
| Groq Qwen3 32B | Cerebras Qwen3 32B | OpenRouter Qwen3 235B:free | Ollama |
| Groq Llama 3.3 70B | Cerebras Llama 3.3 70B | SambaNova Llama 3.3 70B | Ollama |
| DeepSeek R1 (direct) | OpenRouter DeepSeek-R1:free | GitHub Models o3 (compressed) | Ollama |
| Any model | `openrouter/free` auto-router | Ollama (if HW available) | Skip + weight penalty |

---

## R1.20 — Complete API Key Acquisition Checklist

| Key | URL | Time | Priority |
|---|---|---|---|
| ☐ Google AI Studio | aistudio.google.com | 2 min | 🔴 Essential |
| ☐ Groq | console.groq.com | 3 min | 🔴 Essential |
| ☐ OpenRouter | openrouter.ai (add $10) | 5 min | 🔴 Essential |
| ☐ DeepSeek | platform.deepseek.com | 3 min | 🔴 Essential (5M free tokens) |
| ☐ Mistral AI | console.mistral.ai | 3 min | 🟡 Important |
| ☐ SambaNova | cloud.sambanova.ai | 3 min | 🟡 Important |
| ☐ Cerebras | cloud.cerebras.ai | 3 min | 🟡 Important |
| ☐ GitHub Models | github.com/marketplace/models | Instant | 🟡 Important |
| ☐ Upstox API | developer.upstox.com | 10 min | 🔴 Essential |
| ☐ LangSmith | smith.langchain.com | 3 min | 🟡 Important |
| ☐ Finnhub | finnhub.io | 3 min | 🟡 Important |

---

*End of Document — R1 Version 2.0*  
*LLM API providers surveyed: 15+*  
*AI coding/developer tools surveyed: 10+*  
*Critical corrections: OpenRouter 50 RPD, Gemini 2.0 Flash retired, Mistral 2 RPM, Groq deprecations*  
*New providers: GitHub Models, SambaNova, DeepSeek Direct, Cerebras, Fireworks, Vercel*  
*New section: AI Coding & Developer Productivity Tools (R1.14) — 8 tools*
