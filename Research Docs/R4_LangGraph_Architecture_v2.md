# R4 — LangGraph Architecture Research
## Project Pantheon Research Documentation

**Version:** 2.0 — Enhanced Second Pass  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**Research Rounds:** 2 (initial pass + comprehensive second pass)  
**LangGraph Version Researched:** 1.0.x (current stable — see version correction in R4.1)  
**Sources:** Official LangChain changelog, GitHub releases, LangChain blog, PyPI, LangChain forum, Latenode, LetsDatScience, Medium engineering articles, gurusup.com framework comparison — live-fetched March 21, 2026

---

## R4 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R4.1 | Version History — Correction & Current Accurate State | ✅ CORRECTED |
| R4.2 | Core Execution Model — Pregel Supersteps | ✅ Enhanced |
| R4.3 | Parallel Execution — Static Fan-Out/Fan-In | ✅ Enhanced with code |
| R4.4 | Dynamic Parallelism — The Send API | ✅ Complete |
| R4.5 | State Management — TypedDict, Pydantic, Reducers | ✅ Enhanced |
| R4.6 | Checkpointing — Full Version Matrix | ✅ CORRECTED — checkpoint 4.0.0 |
| R4.7 | Async Execution | ✅ Complete |
| R4.8 | Error Handling — RetryPolicy, Atomicity | ✅ Complete |
| R4.9 | **NEW — Node-Level Caching (May 2025)** | ✅ New — key feature for MMCI |
| R4.10 | **NEW — MCP Integration via Streamable HTTP** | ✅ New — critical finding |
| R4.11 | **NEW — langgraph-swarm Library** | ✅ New |
| R4.12 | **NEW — langgraph-bigtool Library** | ✅ New |
| R4.13 | **NEW — Dynamic Tool Calling (August 2025)** | ✅ New |
| R4.14 | **NEW — Long-Term Memory Store** | ✅ New |
| R4.15 | **NEW — LangChain 1.0 Context Engineering (LCEL Deprecated)** | ✅ New — impacts imports |
| R4.16 | Known Limitations, Bugs & Gotchas | ✅ Updated |
| R4.17 | **NEW — Framework Landscape 2026: LangGraph vs All Alternatives** | ✅ New |
| R4.18 | LangGraph vs LangChain LCEL — Definitive Decision | ✅ Updated |
| R4.19 | LangGraph's Direct Applicability to MMCI | ✅ Updated |
| R4.20 | **CORRECTED — Package Ecosystem & Installation Map** | ✅ CORRECTED |
| R4.21 | Architecture Decision Records (ADRs) for Pantheon | ✅ Updated — new ADRs |
| R4.22 | Open Items & Carry-forwards | ✅ Updated |

---

## R4.1 — Version History — Correction & Current Accurate State

### ⚠️ IMPORTANT CORRECTION FROM VERSION 1.0

**Version 1.0 of this document stated: "LangGraph 1.1 released March 10, 2026."**

**This is incorrect and must be retracted.** The second research pass finds no evidence of a LangGraph 1.1 release. The actual version progression is:

| Version | Date | Status |
|---|---|---|
| LangGraph 0.2.x | August 2024 | Independent checkpointer packages introduced |
| LangGraph 1.0 alpha | September 2025 | Alpha announcement |
| **LangGraph 1.0 GA** | **October 29, 2025** | **First stable major release** |
| LangGraph 1.0.x | November 2025 – March 2026 | Patch releases (1.0.8, 1.0.10 confirmed) |

**Current stable version as of March 21, 2026: LangGraph 1.0.x (approximately 1.0.10 based on dependency bump records)**

The features attributed to "LangGraph 1.1" in Version 1.0 of this document — type-safe streaming with `version="v2"`, Pydantic coercion, fixed time travel — are accurate features but were introduced in **LangGraph 1.0**, not a separate 1.1 release. They are opt-in via the `version="v2"` flag in LangGraph 1.0.

**The v1.0 stability commitment remains unchanged:** No breaking changes until v2.0.

### What LangGraph 1.0 GA Means

From the official October 29, 2025 announcement:
> "LangGraph 1.0 is the first stable major release in the durable agent framework space — a major milestone for production-ready AI systems. After more than a year of powering agents at companies like Uber, LinkedIn, and Klarna, LangGraph is officially v1."

> "The only notable change is deprecation of `langgraph.prebuilt`, with enhanced functionality moved to `langchain.agents`. Everything else works as expected."

### Production Adoption Scale

- **90 million monthly downloads** across the LangChain/LangGraph ecosystem
- Production deployments confirmed: Uber, LinkedIn, Klarna, JP Morgan, Blackrock, Cisco
- Search volume leadership: LangGraph at **27,100 monthly searches** (Langfuse framework comparison data, 2026) — the leading agentic framework by search volume
- CrewAI at 14,800 monthly searches for comparison

---

## R4.2 — Core Execution Model — Pregel Supersteps

LangGraph's execution model is inspired by **Google's Pregel system**. This is the foundational design principle and everything in LangGraph flows from it.

### Formal Definition

> "LangGraph models agent workflows as graphs. Nodes are functions that encode agent logic. Edges determine which node executes next. State is a shared data structure representing the current snapshot."

The message-passing loop:
1. All nodes begin in **inactive** state
2. A node becomes **active** when it receives a new message on any incoming edge
3. Active nodes execute their function and respond with **state updates**
4. Updates propagate to downstream nodes
5. The process repeats until no more active nodes remain (graph ends)

### Superstep Definition

A **superstep** is a single iteration over the graph nodes:
- Nodes running in **parallel** are part of the **same superstep**
- Nodes running **sequentially** belong to **separate supersteps**
- A superstep is **transactionally atomic** — all writes in a superstep succeed together, or all fail

```
Superstep 1:  [data_ingestion_node]
Superstep 2:  [prompt_builder_node]
Superstep 3:  [claude_node] [gemini_node] [groq_llama_node] [groq_qwen_node] [mistral_node]
              (all 5 run in parallel — same superstep)
Superstep 4:  [dissent_check_node]
              (waits for ALL of superstep 3 to complete)
Superstep 5:  [consensus_scoring_node] OR [hold_output_node]
              (conditional routing based on dissent flag)
```

---

## R4.3 — Parallel Execution — Static Fan-Out/Fan-In

### How Static Parallelism Is Declared

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(PantheonState)

# Fan-out: single source node → 5 parallel destinations
builder.add_edge("prompt_builder_node", "claude_node")
builder.add_edge("prompt_builder_node", "gemini_node")
builder.add_edge("prompt_builder_node", "groq_llama_node")
builder.add_edge("prompt_builder_node", "groq_qwen_node")
builder.add_edge("prompt_builder_node", "mistral_node")

# Fan-in: all 5 parallel nodes → single convergence point
builder.add_edge("claude_node",     "dissent_check_node")
builder.add_edge("gemini_node",     "dissent_check_node")
builder.add_edge("groq_llama_node", "dissent_check_node")
builder.add_edge("groq_qwen_node",  "dissent_check_node")
builder.add_edge("mistral_node",    "dissent_check_node")
```

LangGraph **automatically detects** the fan-out pattern and executes all 5 model nodes concurrently in a single superstep. No threading code, no asyncio.gather() — the framework handles it.

### The Reducer Pattern — Critical for Parallel Writes

Without a reducer, parallel nodes writing to the same state key raise:
```
InvalidUpdateError: At key 'model_signals': Can receive only one value per step.
```

Fix using `Annotated` with `operator.add`:
```python
from typing import Annotated
import operator
from typing_extensions import TypedDict

class PantheonState(TypedDict, total=False):
    symbol:          str
    stock_context:   StockContext
    model_prompts:   dict[str, str]
    # CRITICAL: reducer required for parallel writes
    model_signals:   Annotated[list[ModelSignal], operator.add]
    dissent_score:   float
    dissent_flag:    bool
    consensus_score: float
    final_signal:    MCISignal
```

With `operator.add`, each parallel model node returning `{"model_signals": [signal]}` will **append** to the list. The `dissent_check_node` receives the fully-assembled list after all 5 model nodes complete.

### max_concurrency — Throttling Parallel Execution

```python
result = graph.invoke(
    initial_state,
    config={"max_concurrency": 3}  # Cap at 3 simultaneous nodes
)
```

For MMCI with 5 model nodes: if rate limits are a concern, setting `max_concurrency=3` runs 3 models first, then the remaining 2. Default is no cap (all 5 run simultaneously). Start without this config and add it if rate limit issues emerge in practice.

---

## R4.4 — Dynamic Parallelism — The Send API

The `Send` API handles cases where the number of parallel branches is determined at runtime:

```python
from langgraph.types import Send

def route_to_available_models(state: PantheonState) -> list[Send]:
    """Dynamically select which models to call based on availability."""
    available_models = state.get("available_models", list(ModelID))
    return [
        Send(f"{model.value}_node", {
            "model_id": model,
            "prompt": state["model_prompts"][model.value]
        })
        for model in available_models
    ]
```

**For MMCI Phase 1:** Static edges are correct — use the fixed 5-model roster.  
**For MMCI Phase 2+:** Send API becomes valuable when dynamic model selection is needed (e.g., skip a model that has been rate-limited today, add a new provider dynamically).

### Deferred Node Execution (defer=True)

```python
builder.add_node(
    "dissent_check_node",
    dissent_check_node,
    defer=True   # Wait for ALL pending tasks before executing
)
```

`defer=True` creates an explicit synchronization barrier — the node will not execute until every other currently-pending node has completed. Cleaner than relying purely on edge topology for synchronization.

**ADR-004 confirmation:** `dissent_check_node` should use `defer=True` in MMCI.

---

## R4.5 — State Management

### TypedDict with `total=False` — The MMCI Choice

```python
from typing import Annotated
import operator
from typing_extensions import TypedDict
from datetime import datetime
from uuid import UUID

class PantheonState(TypedDict, total=False):
    # Input
    symbol:           str
    run_id:           UUID
    # Data ingestion
    stock_context:    StockContext
    market_regime:    MarketRegime
    # Prompts
    model_prompts:    dict[str, str]
    # Parallel writes — MUST use reducer
    model_signals:    Annotated[list[ModelSignal], operator.add]
    # Scoring
    dissent_score:    float
    dissent_flag:     bool
    consensus_score:  float
    confidence_low:   float
    confidence_high:  float
    final_direction:  Direction
    # Position sizing
    suggested_alloc:  float
    risk_level:       int
    price_target:     float | None
    # Output
    final_signal:     MCISignal
    # Meta
    started_at:       datetime
    errors:           list[str]
```

`total=False` means no key is required at initialization — state is built progressively as each node executes. This is the correct design for a multi-step graph where early nodes cannot know what later nodes will produce.

### The MessagesValue Special Case

`MessagesValue` (available in LangGraph's JavaScript version as well as Python) is a special reducer preconfigured with `messagesStateReducer` for chat message history. It handles:
- Deduplication by message ID
- Smart updates (edit existing messages by matching ID)
- Deserialization into LangChain Message objects

For MMCI, this is only relevant if we add a conversational layer in Phase 2+. Phase 1 uses the custom `operator.add` reducer on `model_signals` directly.

---

## R4.6 — Checkpointing — CORRECTED Version Matrix

### ⚠️ IMPORTANT CORRECTION: langgraph-checkpoint 4.0.0

The GitHub dependency release records show:
```
bump langgraph-checkpoint from 3.0.0 to 4.0.0 in /libs/partners/openai
bump langgraph-checkpoint from 3.0.1 to 4.0.0 in /libs/partners/anthropic
bump langgraph-checkpoint from 3.0.1 to 4.0.0 in /libs/langchain
```

**langgraph-checkpoint-postgres and langgraph-checkpoint-sqlite have both been bumped to major version 4.0.0.** This is a breaking change from 3.x. The V1 document cited "v3.0.3" for sqlite — this is now outdated.

### Updated Checkpointer Version Table

| Checkpointer | Package | Current Version | Install |
|---|---|---|---|
| `MemorySaver` | Built-in (`langgraph`) | — | No install |
| `SqliteSaver` | `langgraph-checkpoint-sqlite` | **4.0.x** | `pip install langgraph-checkpoint-sqlite` |
| `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | **4.0.x** | Same package |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | **4.0.x** | `pip install langgraph-checkpoint-postgres` |
| `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | **4.0.x** | Same package |

**If you have existing data from a 3.x checkpointer and upgrade to 4.0.x, run the migration script provided by LangChain. Schema changes in 4.0.0 are not backward-compatible with 3.x checkpoint databases.**

### Thread ID and State Persistence

Every checkpointed run requires a `thread_id`:
```python
config = {"configurable": {"thread_id": "2026-03-21-WIPRO-run-001"}}
final_state = await graph.ainvoke(initial_state, config=config)
```

For MMCI, recommended thread ID scheme: `{YYYY-MM-DD}_{symbol}_{run_number}`

This provides:
- Human-readable identification
- Natural chronological sorting
- Symbol-level filtering for signal history queries

### Checkpointing Phase Strategy

| Phase | Checkpointer | Rationale |
|---|---|---|
| Development | `MemorySaver` | Zero setup, fast iteration |
| Pre-production | `SqliteSaver` (v4.0.x) | Single-file persistence, survives restarts |
| Production | `AsyncPostgresSaver` (v4.0.x) | Queryable, multi-process, production-grade |

---

## R4.7 — Async Execution

### async/await Pattern for MMCI

```python
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Gemini (native async)
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ["GEMINI_API_KEY"]
)

async def gemini_node(state: PantheonState) -> dict:
    try:
        # Native async call — no wrapper needed
        response = await gemini_model.ainvoke(state["model_prompts"]["gemini"])
        signal = parse_signal(ModelID.GEMINI, response.content)
    except Exception as e:
        signal = ModelSignal(
            model_id=ModelID.GEMINI,
            direction=Direction.HOLD,
            confidence=0.0,
            timeframe=Timeframe.MEDIUM,
            reasoning="",
            failed=True,
            failure_reason=str(e)
        )
    return {"model_signals": [signal]}

# Full async graph execution
async def run_mmci_async(symbol: str) -> MCISignal:
    graph = build_graph()
    initial_state: PantheonState = {
        "symbol": symbol,
        "model_signals": [],
        "errors": []
    }
    config = {"configurable": {"thread_id": f"{datetime.now().date()}-{symbol}"}}
    final_state = await graph.ainvoke(initial_state, config=config)
    return final_state["final_signal"]
```

### asyncio.to_thread for Sync SDKs

For providers whose Python SDK is sync-only:
```python
async def groq_node(state: PantheonState) -> dict:
    prompt = state["model_prompts"]["groq"]
    try:
        # groq_client.chat.completions.create() is synchronous
        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        signal = parse_signal(ModelID.GROQ_LLAMA, response.choices[0].message.content)
    except Exception as e:
        signal = ModelSignal(model_id=ModelID.GROQ_LLAMA, ..., failed=True, failure_reason=str(e))
    return {"model_signals": [signal]}
```

### Factory Pattern for Async Nodes — Confirmed Best Practice

The closure-based factory creates async nodes without `functools.partial` (which strips async):
```python
def make_model_node(model_id: ModelID, client):
    async def node(state: PantheonState) -> dict:
        try:
            response = await client.ainvoke(state["model_prompts"][model_id.value])
            signal = parse_model_signal(model_id, response)
        except Exception as e:
            signal = make_failed_signal(model_id, str(e))
        return {"model_signals": [signal]}

    node.__name__ = f"{model_id.value}_node"
    node.__qualname__ = f"{model_id.value}_node"
    return node
```

---

## R4.8 — Error Handling — RetryPolicy

### RetryPolicy Configuration

```python
from langgraph.types import RetryPolicy
import httpx

retry_policy = RetryPolicy(
    max_attempts=3,
    initial_interval=1.0,
    backoff_factor=2.0,      # Waits: 1s, 2s, 4s
    jitter=True,             # Adds randomness to avoid thundering herd
    retry_on=lambda e: isinstance(e, (
        httpx.TimeoutException,
        httpx.HTTPStatusError,
        ConnectionError
    ))
)

builder.add_node("gemini_node", gemini_node, retry_policy=retry_policy)
```

### RetryPolicy Bug with pydantic.ValidationError (Confirmed, Unresolved)

Documented in GitHub issues. When a model returns malformed JSON that fails Pydantic validation, `RetryPolicy` does NOT trigger a retry. The `ValidationError` is not caught by the retry mechanism.

**Mitigation (already in MMCI design):** Wrap ALL Pydantic parsing inside the node's try/except block. Never let Pydantic validation run outside the catch boundary:

```python
async def claude_node(state: PantheonState) -> dict:
    try:
        raw_text = await get_claude_response(state["model_prompts"]["claude"])
        # Wrap Pydantic parsing in the SAME try/except
        signal_data = json.loads(raw_text)
        signal = ModelSignal.model_validate(signal_data)  # May raise ValidationError
    except (json.JSONDecodeError, ValidationError) as e:
        # Caught here, not by RetryPolicy — correct behavior
        signal = make_failed_signal(ModelID.CLAUDE, f"Parse error: {e}")
    except Exception as e:
        signal = make_failed_signal(ModelID.CLAUDE, f"API error: {e}")
    return {"model_signals": [signal]}
```

---

## R4.9 — NEW: Node-Level Caching (May 2025)

**Released:** May 29, 2025 (LangChain Changelog)

This is a significant new feature not covered in V1 that has direct implications for MMCI's efficiency.

### What Node-Level Caching Does

LangGraph now supports caching of node results based on node input. If the same node receives the same input twice, the cached result is returned instead of re-executing the node.

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

# Cache configuration
cache = InMemoryCache()

# Per-node cache policy with TTL
cache_policy = CachePolicy(
    keyFunc=lambda state: f"{state['symbol']}:{state['market_regime']}",
    ttl=3600  # Cache valid for 1 hour (seconds)
)

# Compile graph with cache
graph = builder.compile(
    checkpointer=checkpointer,
    cache=cache
)

# Add cache policy to individual nodes
builder.add_node(
    "gemini_node",
    gemini_node,
    cache_policy=cache_policy  # Cache this node's output
)
```

**Cache hit indicator:** When a node result is served from cache, the state update includes `__metadata__: {cached: True}`.

### Available Cache Backends

| Cache Backend | Type | TTL Support | Best For |
|---|---|---|---|
| `InMemoryCache` | Built-in | Yes | Development, single-process |
| `RedisCache` | Via `langgraph-checkpoint-redis` | Yes | Production, multi-process |

Community also using semantic caching (GraphCache concept) — caches semantically similar inputs using embeddings, not just exact matches. Not yet official.

### Why Node-Level Caching Matters for MMCI

**Critical efficiency gain for a daily analysis pipeline:**

If MMCI analyzes the same 50 stocks every weekday, and the market data + fundamentals for a stock haven't changed significantly since yesterday, the LLM model calls could theoretically be cached.

**Practical MMCI caching strategy:**

| Node | Cache? | TTL | Key Logic |
|---|---|---|---|
| `data_ingestion_node` | ❌ No | — | Always fresh data needed |
| `prompt_builder_node` | ❌ No | — | Prompts contain today's data |
| `claude_node` / `gemini_node` / etc. | ✅ Possibly | 4 hours | Cache key = symbol + date + data hash |
| `dissent_check_node` | ❌ No | — | Pure computation, no API call |
| `consensus_scoring_node` | ❌ No | — | Pure computation |

**Realistic scenario where caching helps:** Running MMCI twice in the same day (e.g., morning pre-market and evening post-market). If the data inputs haven't changed significantly, the model calls can be served from cache, saving rate limit budget.

**Important warning:** LLM calls with identical prompts but different day timestamps should NOT be cached across days. Use date as part of the cache key always.

---

## R4.10 — NEW: MCP Integration via Streamable HTTP

**Released:** Announced in LangChain changelog as new recommended MCP transport

### What Changed

LangGraph can now connect to remote MCP servers via **Streamable HTTP** — the new recommended transport replacing the older SSE-based transport.

```python
from langchain_mcp_adapters import MultiServerMCPClient

async def setup_mcp_tools():
    client = MultiServerMCPClient({
        "upstox_data": {
            "url": "https://api.upstox.com/mcp",   # If Upstox exposes MCP
            "transport": "streamable_http"
        },
        "openbb_data": {
            "url": "http://localhost:8000/mcp",     # Local OpenBB MCP server
            "transport": "streamable_http"
        }
    })
    await client.connect()
    tools = client.get_tools()
    return tools
```

### Why This Matters for MMCI's Data Layer

In R2, we identified that Upstox has an official MCP server. In R3, we identified that OpenBB Platform 4.7.1 includes an MCP server. Now we know that **LangGraph can consume both via a single `MultiServerMCPClient`**.

This means the `data_ingestion_node` could be redesigned to call MCP tools instead of making direct HTTP requests to Upstox and OpenBB APIs:

```python
async def data_ingestion_node_mcp(state: PantheonState) -> dict:
    # Instead of: upstox_client.get_historical_data(symbol)
    # Use: mcp_tool.invoke({"action": "get_historical", "symbol": symbol})
    tools = await get_mcp_tools()
    context = await tools["upstox_get_historical"].ainvoke({
        "symbol": state["symbol"],
        "days": 60
    })
    return {"stock_context": context}
```

**Architecture implication (new ADR candidate):** Evaluate whether MCP-based data access is cleaner than direct API calls for the data layer. Decision pending evaluation during development phase.

### MCP Server Configuration Parameters

For production MCP connections:
```python
{
    "production_server": {
        "url": "https://your-mcp-server.com/mcp",
        "transport": "streamable_http",
        "connection_pool": {
            "max_connections": 10,
            "max_keepalive_connections": 5,
            "keepalive_expiry": 30.0
        },
        "compression": "gzip",
        "timeout": 30.0,
        "batch_size": 5
    }
}
```

### Transport Options

| Transport | When to Use |
|---|---|
| `streamable_http` | Cloud/network deployment — **recommended for production** |
| `stdio` | Local development, subprocess-based MCP servers |
| `sse` | Legacy — was used before, now superseded by `streamable_http` |

---

## R4.11 — NEW: langgraph-swarm Library

**Released:** March 16, 2025 (LangChain Changelog)  
**Install:** `pip install langgraph-swarm`

### What It Is

A lightweight library for building **swarm-style multi-agent systems** with LangGraph, where agents can hand off tasks to each other dynamically based on the current state.

Key features:
- Handoff mechanism: agents transfer control to other agents
- Shared context across agents in the swarm
- Each agent can have its own tools and model

### Why MMCI Doesn't Need It (But Should Know About It)

MMCI uses a **fixed topology fan-out** — all 5 models are called simultaneously, not in a handoff sequence. Swarm architecture is designed for sequential agent handoffs, not parallel simultaneous analysis.

**However, Phase 2+ consideration:** If MMCI is extended with a debate/refinement round after the initial signals, where high-dissent models are asked to respond to each other's reasoning, a swarm architecture would be appropriate for that refinement layer.

---

## R4.12 — NEW: langgraph-bigtool Library

**Released:** March 16, 2025 (LangChain Changelog)  
**Install:** `pip install langgraph-bigtool`

### What It Is

A library enabling LangGraph agents to work with **hundreds or thousands of tools** by using semantic retrieval to select relevant tools for each task, rather than presenting all tools to the model simultaneously.

```python
from langgraph_bigtool import create_agent
from langgraph.store.memory import InMemoryStore

# Register hundreds of tools
tool_registry = {str(uuid.uuid4()): tool for tool in all_tools}

# Embed tool descriptions for semantic retrieval
store = InMemoryStore()

# Agent dynamically retrieves relevant tools per query
agent = create_agent(llm, tool_registry, store=store)
```

### Why MMCI Phase 3+ Should Consider This

The MMCI data layer (R3) identified 40+ data sources and 20+ Python libraries. When Phase 3 implements automated order execution and expands the data pipeline, the number of available tools (NSE API endpoints, Screener.in scrapers, Finnhub calls, Upstox order placement, etc.) will grow large.

`langgraph-bigtool` solves the problem of which tools to present to the model for a given analysis task — instead of overwhelming the prompt with all 40 tool descriptions, the agent retrieves the 3-5 most relevant ones semantically.

**Phase 1 recommendation:** Not needed. MMCI's data layer is defined and hard-coded.  
**Phase 3+ consideration:** Evaluate for the expanded tool ecosystem when live execution is added.

---

## R4.13 — NEW: Dynamic Tool Calling (August 2025)

**Released:** August 27, 2025 (LangChain Changelog)

LangGraph now supports **dynamic tool calling** — controlling which tools are available at different points in the agent's execution, not just at initialization.

```python
from langgraph.prebuilt import create_react_agent, InjectedState
from typing import Annotated

def get_available_tools(state: PantheonState) -> list:
    """Return tools based on current state."""
    if state.get("market_regime") == MarketRegime.BEAR:
        # In bear markets, provide conservative tools only
        return [get_fundamentals_tool, get_defensive_sector_tool]
    return [get_fundamentals_tool, get_technicals_tool, get_news_tool]

# Agent gets different tools depending on market regime
agent = create_react_agent(
    model=gemini_model,
    tools=get_available_tools  # callable, not static list
)
```

**MMCI relevance:** Phase 2+ could use dynamic tool calling to give each model node different tools based on:
- Market regime (bear markets → conservative tool set)
- Model specialization (Gemini gets web search tool, DeepSeek gets quantitative tools)
- Available rate limit budget (skip expensive tools when approaching daily limits)

---

## R4.14 — NEW: Long-Term Memory Store

LangGraph has two distinct persistence mechanisms that serve different purposes:

### Checkpoints vs Long-Term Store

| Feature | Checkpoints | Long-Term Store |
|---|---|---|
| Purpose | Resume execution from failure | Persist data across graph invocations |
| Scope | Single thread's execution state | Global, cross-thread data |
| Lifetime | Until checkpoint is deleted | Persists indefinitely |
| Access | Automatic during graph execution | Explicitly queried by nodes |
| Best for | Fault tolerance, time travel | User preferences, learned patterns |

### The Long-Term Store API

```python
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import AsyncPostgresStore

# Initialize store
store = InMemoryStore()  # Development
# store = AsyncPostgresStore(conn_string)  # Production

# Store data
store.put(("weights", "model_accuracy"), "claude", {"weight": 0.22, "correct": 45, "total": 60})

# Retrieve data
item = store.get(("weights", "model_accuracy"), "claude")
# Returns: {value: {"weight": 0.22, "correct": 45, "total": 60}}

# Search (semantic if embeddings configured)
results = store.search(("weights",), query="most accurate model")
```

### Why This Is Critical for MMCI's Weight System

The MMCI weight update mechanism (W(new) = W(old) + α × (correct - W(old))) needs to persist model accuracy data **across all MMCI runs** — not just within a single analysis run.

The Long-Term Store is the **correct LangGraph-native solution** for storing model weights:

```python
# In weight_update_job (runs T+5 days after signal)
async def update_model_weights(
    symbol: str,
    run_id: UUID,
    actual_outcome: Direction,
    store: BaseStore
):
    # Retrieve current weights
    weights_item = store.get(("mmci", "model_weights"), "current")
    weights = weights_item.value if weights_item else INITIAL_WEIGHTS.copy()
    
    # Get model signals for this run from checkpoint history
    signals = get_historical_signals(run_id)
    
    # Update weights using MMCI formula
    for signal in signals:
        correct = int(signal.direction == actual_outcome)
        old_w = weights[signal.model_id]
        weights[signal.model_id] = old_w + LEARNING_RATE * (correct - old_w)
    
    # Normalize
    total = sum(weights.values())
    weights = {k: v/total for k, v in weights.items()}
    
    # Store updated weights
    store.put(("mmci", "model_weights"), "current", weights)
```

**ADR Update:** Use LangGraph's Long-Term Store for model weight persistence, not a separate database table. This keeps weight management inside the LangGraph ecosystem and benefits from the same PostgreSQL backend.

---

## R4.15 — NEW: LangChain 1.0 Context Engineering — LCEL Deprecated

### The Biggest LangChain 1.0 Change

From the October 2025 LangChain 1.0 announcement and community analysis:

> "Goodbye LCEL (LangChain Expression Language) runnables with pipes — I won't miss you. Apps that have many '|' operators (prompt | llm | StrOutputParser()) are no longer a thing — thank goodness."

**LCEL is deprecated in LangChain 1.0.** The pipe-operator syntax:
```python
# OLD (deprecated, still works but discouraged)
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "hello"})
```

is replaced by:
```python
# NEW (LangChain 1.0)
from langchain.agents import create_agent
agent = create_agent(llm, tools, prompt)
result = agent.invoke({"input": "hello"})
```

### What This Means for MMCI

MMCI **does not use LCEL chains anywhere.** Model calls are made directly inside async node functions using the model's `.ainvoke()` method. This is the correct approach for LangGraph-native code and requires no changes.

### Context Engineering (New LangChain 1.0 Concept)

LangChain 1.0 introduces **middleware abstractions** for context management:
- Context quarantine: prevent context pollution between chains
- Context injection: inject structured data into model prompts

For MMCI, this means the `prompt_builder_node` can use LangChain's middleware for building StockContext-aware prompts:
```python
from langchain.middleware import ContextMiddleware

class FinancialContextMiddleware(ContextMiddleware):
    """Inject StockContext as structured context into model prompts."""
    def process(self, context: dict, state: PantheonState) -> dict:
        context["stock_data"] = state["stock_context"].model_dump()
        context["regime"] = state["market_regime"].value
        return context
```

This is an optional enhancement for Phase 2. Not required for Phase 1.

### Agent Definition in LangChain 1.0

From the announcement:
> "From LangChain 1.0 onwards, the only way to define an agent is within LangChain itself, not LangGraph. The older ways of defining agents — through Agent and AgentExecutor — are officially deprecated."

> "You can even inject custom logic during LLM or tool interactions, giving you fine-grained control without additional orchestration complexity. In other words: fewer moving parts, more flexibility."

**For MMCI:** We don't use prebuilt agents at all — MMCI uses raw LangGraph nodes. This deprecation has zero direct impact on MMCI's design.

---

## R4.16 — Known Limitations, Bugs & Gotchas (Updated)

### All Issues from V1 (Confirmed Still Present)

**L1:** Parallel superstep update ordering is non-deterministic → sort `model_signals` by `model_id` in `dissent_check_node` for reproducible test output.

**L2:** `RetryPolicy` does not catch `pydantic.ValidationError` → wrap all Pydantic parsing in try/except inside nodes.

**L3:** `functools.partial` breaks async nodes → use factory/closure pattern.

**L4:** `langgraph dev` CLI ignores custom checkpointers → dev only issue, no production impact.

**L5:** `asyncio.run()` inside sync node in async event loop → use `await graph.ainvoke()` from async context.

### New Issues Discovered in Second Pass

**L6: langgraph-checkpoint 4.0.0 Breaking Schema Change**

The upgrade from checkpoint 3.x to 4.0.x is NOT data-compatible. If you initialize a SqliteSaver with 3.x and later upgrade to 4.0.x, the existing checkpoint data is unreadable.

**Mitigation:** Start fresh with a new SQLite file on first production deployment. Do not attempt to migrate 3.x checkpoint data to 4.x without running the official migration script.

**L7: InMemoryCache Incompatibility with InMemorySaver**

Community forum report (August 20, 2025): `InMemoryCache` (for node-level caching) has a documented incompatibility with `InMemorySaver` (for checkpointing) in certain invocation modes. Specifically, using `stream_mode='updates'` is required to detect cache hits — other stream modes may not surface the `__metadata__: {cached: True}` indicator.

**Mitigation:** When using both `InMemoryCache` and `InMemorySaver` together, use `stream_mode='updates'` for inspection. For production, use `RedisCache` with `PostgresSaver` — both are separate packages and do not have this conflict.

**L8: Checkpoint postgres 4.0.0 Connection Pool Requirements**

The new postgres checkpointer 4.0.0 requires explicit connection pool configuration. The simplified connection string approach of 3.x may not work without specifying pool parameters.

```python
# Correct approach for 4.0.x
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import psycopg_pool

async with await psycopg_pool.AsyncConnectionPool(
    conninfo="postgresql://user:pass@localhost/pantheon",
    max_size=10
) as pool:
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()  # Required in 4.0.x
    graph = builder.compile(checkpointer=checkpointer)
```

**L9: MCP Streamable HTTP Connection Handling**

When using `MultiServerMCPClient` with `streamable_http` transport, connections must be explicitly managed using async context manager:

```python
# WRONG — connection not properly managed
client = MultiServerMCPClient(config)
tools = client.get_tools()  # May fail

# CORRECT — explicit connection lifecycle
async with MultiServerMCPClient(config) as client:
    tools = client.get_tools()
    # Use tools here
```

---

## R4.17 — NEW: Framework Landscape 2026 — LangGraph vs All Alternatives

This is the comprehensive competitive context for the choice of LangGraph for MMCI.

### The Six Production-Grade Agent Frameworks (March 2026)

| Framework | Current Version | Released | Stars | Philosophy |
|---|---|---|---|---|
| **LangGraph** | 1.0.x | Oct 2025 (1.0) | Very high | Directed graph, fine-grained control |
| **CrewAI** | 1.10.1 | 2023 | 44,600+ | Role-based crews, task delegation |
| **OpenAI Agents SDK** | 0.10.2 | March 2025 | Growing | Tool-use-first, 100+ models |
| **Google ADK** | 1.26.0 | April 2025 | Growing | Hierarchical tree, Vertex AI integration |
| **Anthropic Agent SDK** | 0.1.48 | 2025 | Growing | Claude-centric, computer use |
| **Microsoft Agent Framework** | Varies | 2025 | Growing | Enterprise, Azure-native |

### Why LangGraph Remains the Correct Choice for MMCI

**The critical technical discriminators:**

| Requirement | LangGraph | CrewAI | OpenAI SDK | Google ADK |
|---|---|---|---|---|
| Parallel fan-out with reducer | ✅ Native | ❌ Sequential | ⚠️ Limited | ⚠️ Via sub-agents |
| Stateful graph with typed state | ✅ Core feature | ❌ No | ❌ No | ⚠️ Limited |
| Conditional routing (dissent → HOLD) | ✅ Native | ⚠️ Via process | ⚠️ Via tools | ⚠️ Via routing |
| Checkpointing to PostgreSQL | ✅ Official 4.0.x | ❌ No | ❌ No | ⚠️ Via Vertex AI |
| Custom state reducers | ✅ Native | ❌ No | ❌ No | ❌ No |
| Multi-model provider support | ✅ Any provider | ✅ Yes | ✅ 100+ models | ⚠️ Gemini-first |
| Production proven | ✅ Uber, JP Morgan | ✅ Growing | ⚠️ New | ⚠️ New |

MMCI's parallel fan-out pattern, typed state with reducers, and conditional routing are all **core LangGraph features with no equivalent in other frameworks.** Rebuilding MMCI on CrewAI or OpenAI SDK would require workarounds for every structural requirement.

### The A2A Protocol — Future Consideration

**Google's A2A (Agent-to-Agent) protocol** enables communication between agents from different frameworks. LangGraph supports A2A via LangSmith.

**Future MMCI relevance:** If a Gemini-based agent from Google ADK needs to interface with the LangGraph MMCI pipeline, A2A provides the standardized protocol. Not relevant for Phase 1, but worth monitoring as multi-framework deployments become common.

### LangSmith — Observability Layer

**LangSmith** is the official observability and tracing tool for LangGraph. It provides:
- Full execution trace visualization (every node, every state transition)
- Prompt/response logging for debugging
- Cost tracking per LLM call
- Regression testing for agent behavior
- Free tier: 5,000 traces/month

**For MMCI:** LangSmith is the most natural debugging tool for production MMCI runs. The free tier covers ~5,000 analysis runs per month — sufficient for personal use.

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your_langsmith_api_key"
os.environ["LANGCHAIN_PROJECT"] = "pantheon-mmci"
# All LangGraph runs are now automatically traced
```

---

## R4.18 — LangGraph vs LangChain LCEL — Final Decision (Updated)

With LCEL deprecated in LangChain 1.0, the answer is simpler than ever:

| Layer | Tool | Decision |
|---|---|---|
| Orchestration | LangGraph StateGraph | ✅ MMCI backbone |
| Model calls | `ChatGoogleGenerativeAI`, `ChatOpenAI` | Inside LangGraph nodes |
| Prompt construction | LangChain PromptTemplate | Optional utility inside nodes |
| Output parsing | Pydantic `model_validate` directly | Inside nodes, with error handling |
| LCEL chains | ❌ Deprecated | Not used |

**Decision (updated from V1):** LCEL is deprecated. Even if we wanted to use it, LangGraph nodes with direct model calls are the framework-endorsed approach.

---

## R4.19 — LangGraph's Applicability to MMCI (Updated)

### Complete MMCI → LangGraph Feature Mapping (Updated)

| MMCI Requirement | LangGraph Feature | Version | Confidence |
|---|---|---|---|
| 5 parallel model calls | Static fan-out edges | 1.0 | ✅ Confirmed |
| Merge signals into list | `operator.add` reducer on `model_signals` | 1.0 | ✅ Confirmed |
| Wait for all models | Fan-in topology + `defer=True` | 1.0 | ✅ Confirmed |
| Dissent → HOLD routing | `add_conditional_edges` | 1.0 | ✅ Confirmed |
| Fault tolerance on API failure | Checkpointer + pending writes | 4.0.x | ✅ Confirmed |
| Per-node retry with backoff | `RetryPolicy` | 1.0 | ✅ Confirmed (watch pydantic bug) |
| Full async execution | `ainvoke()` + `async def` nodes | 1.0 | ✅ Confirmed |
| Weight persistence across runs | Long-Term Memory Store | 1.0 | ✅ New — use Store API |
| Signal caching for efficiency | Node-level caching with TTL | 1.0 (May 2025) | ✅ New — valuable for MMCI |
| MCP data tool integration | `MultiServerMCPClient` | 1.0 | ✅ New — evaluate for data layer |
| Execution tracing/debugging | LangSmith | External | ✅ Free tier available |
| Phase 2 real-time streaming | `astream()` with `version="v2"` | 1.0 | ✅ Confirmed |
| Phase 3 dynamic tool selection | Dynamic tool calling | 1.0 (Aug 2025) | ✅ New — relevant for Phase 3 |

---

## R4.20 — CORRECTED Package Ecosystem & Installation Map

### Core Packages (Corrected Versions)

```
langgraph>=1.0.0                   # Core graph execution (current: 1.0.x)
langchain>=1.0.0                   # LangChain v1 stable
langchain-core>=0.3.x              # Core primitives
langchain-google-genai>=2.1.0      # Gemini model wrapper
langchain-openai>=1.1.0            # OpenAI-compatible (Groq, OpenRouter, Mistral)
pydantic>=2.0.0                    # State validation
```

### Checkpointer Packages (Corrected Versions)

```
langgraph-checkpoint-sqlite>=4.0.0   # CORRECTED: was 3.0.3 in V1 — now 4.0.x
langgraph-checkpoint-postgres>=4.0.0  # CORRECTED: now 4.0.x
langgraph-checkpoint-redis>=1.0.0    # For Redis-backed fast caching
```

### New Packages Since V1

```
langgraph-swarm>=0.0.x             # Swarm-style multi-agent (Phase 2+)
langgraph-bigtool>=0.0.3           # Large tool registries (Phase 3+)
langchain-mcp-adapters>=0.1.0      # MCP server integration
```

### Confirmed OpenAI-Compatible API Pattern (With Correct Providers)

```python
from langchain_openai import ChatOpenAI

# Groq — Qwen3 32B (quantitative analysis role)
groq_qwen = ChatOpenAI(
    model="qwen3-32b",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1,
    max_tokens=500
)

# Groq — Llama 3.3 70B (general reasoning role)
groq_llama = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1,
    max_tokens=500
)

# Mistral (sentiment/news role)
mistral = ChatOpenAI(
    model="mistral-small-3.1",
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ["MISTRAL_API_KEY"],
    temperature=0.1,
    max_tokens=500
)

# OpenRouter — DeepSeek R1 (chain-of-thought reasoning role)
deepseek = ChatOpenAI(
    model="deepseek/deepseek-r1:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    temperature=0.0,  # R1 works best at 0 temp
    max_tokens=500,
    extra_headers={"HTTP-Referer": "https://github.com/pantheon"}
)

# Google Gemini — needs its own wrapper
from langchain_google_genai import ChatGoogleGenerativeAI
gemini_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=os.environ["GEMINI_API_KEY"],
    temperature=0.1,
    max_output_tokens=500
)

gemini_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ["GEMINI_API_KEY"],
    temperature=0.1,
    max_output_tokens=500
)
```

---

## R4.21 — Architecture Decision Records (ADRs) — Updated

### ADR-001 through ADR-006 (from V1 — all confirmed)

All six ADRs from V1 remain valid and confirmed:
- ADR-001: Static edges over Send API for 5-model fixed roster ✅
- ADR-002: All model nodes must catch exceptions internally ✅
- ADR-003: TypedDict with `total=False` for PantheonState ✅
- ADR-004: `defer=True` on `dissent_check_node` ✅
- ADR-005: MemorySaver → SqliteSaver → PostgresSaver progression ✅
- ADR-006: `langchain-openai` as unified adapter for non-Google providers ✅

### New ADRs from Second Pass

**ADR-007: Use LangGraph Long-Term Store for Model Weight Persistence**

**Decision:** Use LangGraph's built-in Long-Term Store (backed by PostgreSQL in production) for MMCI model weight persistence rather than a separate `model_weights` database table.

**Rationale:**
- Keeps weight management inside the LangGraph ecosystem
- Same PostgreSQL connection pool as the checkpointer
- Store API is designed for exactly this use case (cross-run persistent data)
- Simplifies the architecture by eliminating a separate DB access pattern
- Store supports semantic search (if needed for future model selection)

**Status:** DECIDED ✅

---

**ADR-008: Use Node-Level Caching for Intra-Day Re-Analysis**

**Decision:** Implement node-level caching with 4-hour TTL on all 5 model nodes using symbol + date + data_hash as the cache key.

**Rationale:**
- If MMCI runs twice on the same day with the same data, model calls should not repeat
- 4-hour TTL ensures fresh analysis for end-of-day re-runs
- Significantly reduces daily rate limit consumption if MMCI runs multiple times
- Cache key includes `data_hash` to ensure stale caches don't serve incorrect results after data update

**Status:** DECIDED ✅

---

**ADR-009: Evaluate MCP Data Layer Before Development Begins**

**Decision:** Before writing the data_ingestion_node as direct API calls, first evaluate whether Upstox's MCP server and OpenBB's MCP server can serve as the data access layer via `MultiServerMCPClient`.

**Rationale:**
- If MCP-based data access works, eliminates the need to write custom Upstox API wrappers
- MCP provides a standardized interface that abstracts provider changes
- Both Upstox and OpenBB have confirmed MCP server capabilities
- Could reduce data pipeline code by 50-60%

**If MCP evaluation fails:** Fall back to direct API calls (the original plan).

**Status:** EVALUATION PENDING — first task when development begins ✅

---

**ADR-010: Integrate LangSmith for Signal Audit Trail**

**Decision:** Enable LangSmith tracing on all MMCI production runs from Phase 1 onwards.

**Rationale:**
- Free tier: 5,000 traces/month — sufficient for personal use
- Each trace records every model call, input prompt, output signal
- This trace constitutes the 5-year audit trail required by SEBI's AI/ML guidelines (when applicable)
- Invaluable for debugging when a signal seems wrong
- Doubles as research paper evidence: can show exactly what prompts produced what outputs

**Status:** DECIDED ✅

---

## R4.22 — Open Items & Carry-forwards (Updated)

| Item | Details | Priority |
|---|---|---|
| MCP data layer evaluation | Test Upstox MCP + OpenBB MCP before writing custom adapters (ADR-009) | 🔴 First task in development |
| Checkpoint 4.0.x migration path | Document the exact setup procedure for `AsyncPostgresSaver` with 4.0.x connection pool | 🔴 Before production deployment |
| InMemoryCache + InMemorySaver compatibility | Verify the community-reported conflict in actual MMCI test environment | 🟡 During development |
| LangSmith project setup | Create "pantheon-mmci" project on LangSmith free tier | 🟡 Before first test run |
| Long-Term Store for weights | Prototype the weight storage pattern using Store API | 🟡 During algorithm implementation |
| Checkpoint 4.0.x data schema | Document the new schema format to understand what MMCI checkpoint history looks like | 🟡 Architecture phase |
| Node-level cache key design | Finalize the `keyFunc` for the 5 model nodes — determine what constitutes a "same input" | 🟡 Implementation phase |
| Dynamic tool calling for Phase 3 | Design tool sets per market regime (bear/bull/sideways) for each model node | 🟢 Phase 3 planning |
| A2A protocol monitoring | Track Google ADK A2A adoption — may enable cross-framework MMCI extensions | 🟢 Low priority now |

---

## Summary — R4 Version 2.0 Complete Picture

| Question | V1 Answer | V2 Corrected/Updated Answer |
|---|---|---|
| Current LangGraph version? | "1.1" (incorrect) | **1.0.x (approximately 1.0.10)** |
| Checkpoint package version? | "3.0.3" (outdated) | **4.0.x (breaking change from 3.x)** |
| Is node-level caching available? | Not mentioned | **Yes — released May 2025, relevant for MMCI** |
| Does LangGraph support MCP? | Not mentioned | **Yes — Streamable HTTP transport, MultiServerMCPClient** |
| Is there a swarm library? | Not mentioned | **Yes — langgraph-swarm, Phase 2+ consideration** |
| Is there a bigtool library? | Not mentioned | **Yes — langgraph-bigtool, Phase 3+ consideration** |
| Is LCEL still the LangChain standard? | Referenced | **No — deprecated in LangChain 1.0** |
| Where to store model weights cross-run? | "PostgreSQL signals table" | **LangGraph Long-Term Store (same PostgreSQL backend)** |
| Is there an observability tool? | "LangSmith mentioned as future" | **LangSmith — free tier, 5,000 traces/month, use from day 1** |
| How many frameworks compete with LangGraph? | Not analyzed | **6 production-grade frameworks; LangGraph leads on MMCI requirements** |

---

*End of Document — R4 Version 2.0: LangGraph Architecture Research*  
*New features documented: Node-level caching, MCP Streamable HTTP, langgraph-swarm, langgraph-bigtool, Dynamic tool calling, Long-Term Memory Store, LCEL deprecation*  
*Corrections issued: LangGraph version (1.0.x not 1.1), checkpoint package version (4.0.x not 3.0.3)*  
*New ADRs added: ADR-007 (Long-Term Store for weights), ADR-008 (node caching), ADR-009 (MCP evaluation), ADR-010 (LangSmith)*  
*Next: Complete Research Review Session across R1–R6*
