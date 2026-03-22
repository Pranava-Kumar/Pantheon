# R4 — LangGraph Architecture Research
## Project Pantheon Research Documentation

**Version:** 1.0  
**Date:** March 21, 2026  
**Status:** Research Complete — Pending Review  
**LangGraph Version Researched:** 1.1 (current stable, Python)  
**Sources:** Official LangChain docs, LangGraph GitHub releases, LangChain blog, community forum, PyPI, production engineering articles — live-fetched March 21, 2026

---

## R4 Sub-Task Breakdown

| Sub-task | Topic | Status |
|---|---|---|
| R4.1 | Version History & Current Stable State | ✅ Complete |
| R4.2 | Core Execution Model — Pregel Supersteps | ✅ Complete |
| R4.3 | Parallel Execution — Static Fan-Out/Fan-In | ✅ Complete |
| R4.4 | Dynamic Parallelism — The Send API (Map-Reduce) | ✅ Complete |
| R4.5 | State Management — TypedDict, Pydantic, Reducers | ✅ Complete |
| R4.6 | Checkpointing & Persistence Layer | ✅ Complete |
| R4.7 | Async Execution — ainvoke, astream, asyncio | ✅ Complete |
| R4.8 | Error Handling — RetryPolicy, Superstep Atomicity | ✅ Complete |
| R4.9 | Known Limitations, Bugs & Gotchas | ✅ Complete |
| R4.10 | LangGraph vs LangChain LCEL — When to Use Which | ✅ Complete |
| R4.11 | LangGraph's Direct Applicability to MMCI | ✅ Complete |
| R4.12 | Package Ecosystem & Installation Map | ✅ Complete |
| R4.13 | Architecture Decision Records (ADRs) for Pantheon | ✅ Complete |
| R4.14 | Open Items & Carry-forwards | ✅ Complete |

---

## R4.1 — Version History & Current Stable State

### Timeline

| Date | Milestone |
|---|---|
| Late 2023 | LangGraph first released as open-source library |
| August 2024 | v0.2 released — independent checkpointer packages introduced |
| October 2025 | **LangGraph 1.0 released** — first stable major version, full backward compatibility commitment, langgraph.prebuilt deprecated |
| October 2025 | LangChain 1.0 released alongside — agents now run on LangGraph runtime under the hood |
| March 10, 2026 | **LangGraph 1.1 released** — type-safe streaming v2, type-safe invoke v2 (opt-in), Pydantic/dataclass output coercion |

### Current State (March 2026)

- **Stable version:** LangGraph 1.1 (Python), with LangGraph 1.0.x as the baseline
- **API stability:** v1.0 committed to no breaking changes until v2.0
- **LangGraph 1.1 new features (opt-in, fully backward-compatible):**
  - `version="v2"` flag on `invoke()`/`stream()` → returns typed `GraphOutput` object with `.value` and `.interrupts` instead of plain dict
  - `StreamPart` TypedDict for all streaming modes
  - Pydantic model / dataclass output coercion when state schema is typed
  - Fixed time-travel with interrupts and subgraphs

- **langgraph.prebuilt status:** Deprecated in v1.0. All prebuilt agents moved to `langchain.agents`. The MMCI system doesn't use prebuilt agents, so this deprecation has zero impact on us.

- **Production adoption:** Uber, LinkedIn, Klarna, JP Morgan, Blackrock, Cisco confirmed production deployments. 90M monthly downloads across the LangChain/LangGraph ecosystem.

---

## R4.2 — Core Execution Model — Pregel Supersteps

LangGraph's execution model is inspired by **Google's Pregel system** — a graph computation framework designed for large-scale graph processing. Understanding this model is essential for designing the MMCI graph correctly.

### What is a Superstep?

A **superstep** is LangGraph's fundamental execution unit. It is a batch of nodes that:
- Can execute concurrently with each other within the batch
- All execute before any node in the next superstep can begin
- Are treated **transactionally** — either all succeed or the entire superstep fails atomically

This is the single most important architectural concept in LangGraph. Everything else flows from it.

### How Supersteps Work Visually

```
START → [node_a]                         ← Superstep 1 (single node)
         ↓         ↓         ↓
   [node_b]  [node_c]  [node_d]           ← Superstep 2 (parallel — all three run concurrently)
         ↓         ↓         ↓
              [node_e]                   ← Superstep 3 (waits for all of superstep 2 to complete)
```

Nodes b, c, d run simultaneously. Node e does not start until ALL of b, c, d have finished.

### Pregel-Inspired Message Passing

At each superstep, nodes:
1. Receive the current state (shared across all nodes)
2. Perform their work
3. Return a **partial state update** (a dict of which keys to update)
4. LangGraph merges all partial updates back into the state using **reducer functions**

This message-passing model is why LangGraph doesn't use function arguments between nodes — everything passes through the shared, typed state object.

---

## R4.3 — Parallel Execution — Static Fan-Out/Fan-In

This is the mechanism we designed the MMCI agent graph around. Here is the complete, verified specification.

### How Static Parallelism Is Declared

Static parallelism is achieved simply by adding multiple edges from one node to multiple destination nodes:

```python
builder.add_edge("prompt_builder_node", "claude_node")
builder.add_edge("prompt_builder_node", "gemini_node")
builder.add_edge("prompt_builder_node", "groq_llama_node")
builder.add_edge("prompt_builder_node", "groq_qwen_node")
builder.add_edge("prompt_builder_node", "mistral_node")
```

LangGraph **automatically detects** this fan-out pattern and executes the destination nodes concurrently in the same superstep. No explicit thread management, no asyncio.gather() — the framework handles it.

### Fan-In — Converging Parallel Branches

To fan back in, add edges from all parallel nodes to the same downstream node:

```python
# All model nodes → dissent_check_node
builder.add_edge("claude_node", "dissent_check_node")
builder.add_edge("gemini_node", "dissent_check_node")
builder.add_edge("groq_llama_node", "dissent_check_node")
# etc.
```

LangGraph automatically waits for all upstream nodes to complete before executing `dissent_check_node`. This is the synchronization barrier.

### Critical: Reducer Functions for Parallel State Writes

**The most common mistake in parallel LangGraph graphs.** When multiple parallel nodes write to the same state key, they will conflict without a reducer. The error is explicit:
```
At key 'model_signals': Can receive only one value per step.
```

The fix is to annotate the state key with a reducer function using Python's `Annotated` type:

```python
from typing import Annotated
import operator
from typing_extensions import TypedDict

class PantheonState(TypedDict):
    model_signals: Annotated[list, operator.add]   # list accumulation reducer
```

With `operator.add` as the reducer, each parallel model node returning `{"model_signals": [signal]}` will have its result **appended** to the list rather than overwriting it. This is exactly the pattern needed for MMCI's `model_signals` field.

### State Update Ordering in Parallel Supersteps — Important Warning

**Update ordering from parallel nodes is non-deterministic.** If node B and node C both complete in the same superstep, their state updates are merged in an unspecified order. This is by design.

For MMCI, this is fine because:
- The `model_signals` list uses `operator.add` reducer (order of append doesn't matter mathematically)
- The dissent score and consensus score are computed from the full list after all nodes complete
- The final `MCISignal` is deterministic regardless of append order

If ordering of parallel outputs ever matters, the recommended pattern is to write outputs with an identifying key and sort in the fan-in node.

### Multi-Step Parallel Branches

LangGraph handles branches with unequal lengths correctly. If branch A has steps A1→A2→A3 and branch B has B1, the graph will wait until A3 AND B1 both complete before the fan-in node runs:

```
                ┌── A1 ─→ A2 ─→ A3 ──┐
[fan_out_node] ─┤                      ├─→ [fan_in_node]
                └── B1 ───────────────┘
```

This handles the case where some model API calls take longer than others naturally.

### max_concurrency Configuration

LangGraph provides a `max_concurrency` parameter to cap the number of simultaneously executing nodes:

```python
graph.invoke(state, config={"max_concurrency": 3})
```

For MMCI with 5 model nodes in parallel, this parameter lets us throttle to fewer simultaneous API calls if needed (e.g., on systems with limited resources). Default is unlimited parallelism.

---

## R4.4 — Dynamic Parallelism — The Send API (Map-Reduce)

The `Send` API is the advanced version of parallelism for use cases where the number of parallel branches is **not known at graph design time** but depends on runtime state.

### Send API — Core Concept

```python
from langgraph.types import Send

def route_to_models(state: PantheonState) -> list[Send]:
    # Determine which models to use based on state (runtime decision)
    active_models = state.get("active_models", list(ModelID))
    return [
        Send(f"{model.value}_node", {"model_id": model, "prompt": state["model_prompts"][model.value]})
        for model in active_models
    ]
```

Each `Send` object specifies:
- The target node name
- A **partial state** to pass to that specific instance of the node (can differ from the main graph state)

When the router returns a list of `Send` objects, LangGraph runs all of them in parallel.

### Send API vs Static Edges — When to Use Each

| Scenario | Use Static Edges | Use Send API |
|---|---|---|
| Fixed set of parallel operations | ✅ | |
| Variable number of parallel operations | | ✅ |
| All parallel branches do the same operation | | ✅ |
| Each parallel branch has unique logic | ✅ | |
| Simplicity and debuggability preferred | ✅ | |
| Map-reduce over a dynamic list | | ✅ |

**For MMCI's core design:** Static edges are the right choice. We have a fixed set of 5 models. The graph structure is known at compile time. Send API adds unnecessary complexity for our use case.

**However, Send API becomes valuable in Phase 2** when we want to dynamically select which models to include based on factors like which APIs are available, rate limit status, or model accuracy history.

### Deferred Node Execution

LangGraph 1.0 introduced `defer=True` on node definitions. A deferred node will NOT execute until all other pending tasks in the graph are complete:

```python
builder.add_node("dissent_check_node", dissent_check_node, defer=True)
```

This is equivalent to a synchronization barrier. It ensures that `dissent_check_node` executes only after ALL model signal nodes have completed — even if some branches have more steps than others.

**For MMCI:** This is cleaner than relying purely on the fan-in edge topology. Setting `defer=True` on `dissent_check_node` guarantees it waits for all model nodes, regardless of how the graph edges are structured.

---

## R4.5 — State Management — TypedDict, Pydantic, Reducers

### Three Ways to Define State in LangGraph

**1. TypedDict (most common, recommended for MMCI):**
```python
from typing_extensions import TypedDict
class PantheonState(TypedDict, total=False):
    symbol: str
    model_signals: Annotated[list[ModelSignal], operator.add]
    consensus_score: float
```

**2. Pydantic BaseModel (with LangGraph 1.1 type-safe mode):**
```python
from pydantic import BaseModel
class PantheonState(BaseModel):
    symbol: str = ""
    model_signals: list[ModelSignal] = []
    consensus_score: float = 0.0
```

When using `version="v2"` in invoke(), LangGraph automatically coerces the output to the Pydantic model type.

**3. Python dataclass:**
```python
from dataclasses import dataclass, field
@dataclass
class PantheonState:
    symbol: str = ""
    model_signals: list = field(default_factory=list)
```

### Recommended: TypedDict with `total=False`

For MMCI, `TypedDict` with `total=False` is the right choice because:
- Fields are populated progressively across nodes — not all fields exist at the start
- `total=False` means no key is required — matches our progressive graph execution model
- Lighter than Pydantic (no validation overhead on every state transition)
- Direct compatibility with all LangGraph APIs without version flags

### Reducers — The Full List of Options

| Reducer | Import | Effect | Use in MMCI |
|---|---|---|---|
| `operator.add` | `import operator` | Concatenates lists | `model_signals` accumulation |
| `operator.add` | `import operator` | Adds numbers | Not needed |
| `add_messages` | `from langgraph.graph.message import add_messages` | Smart message merging | Only if using message history |
| Custom function | Defined inline | Any merge logic | Could use for weighted signal merging |
| None (default) | — | Last write wins (overwrite) | All non-parallel fields |

### State Schema Is Static

An important constraint: **the state schema is defined at compile time, not at runtime**. You cannot add new keys to the state during execution. All keys must be declared in the TypedDict/Pydantic model before compilation.

This is fine for MMCI — our state schema is fully known. But it means we cannot dynamically add a new model's output key if we discover a new model at runtime. The solution is to use a list field with a reducer (which we already do via `model_signals`).

---

## R4.6 — Checkpointing & Persistence Layer

### What Checkpointing Provides

Checkpointing saves the graph state to a storage backend at every node execution step. This enables:
- **Fault tolerance**: If a node fails mid-execution, resume from the last successful step
- **Human-in-the-loop**: Pause execution indefinitely, await human input, resume at exact state
- **Time travel**: Replay any previous state to debug or branch alternate execution paths
- **Multi-turn workflows**: Persist state across multiple invocations in the same thread

### Available Checkpointers

| Checkpointer | Package | Best For | Install |
|---|---|---|---|
| `MemorySaver` | Built-in (no install) | Development, testing, demos | — |
| `SqliteSaver` | `langgraph-checkpoint-sqlite` (v3.0.3) | Local dev, single-machine production | `pip install langgraph-checkpoint-sqlite` |
| `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | Async applications | Same package |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | Production, multi-worker, queryable | `pip install langgraph-checkpoint-postgres` |
| `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | Async + production | Same package |
| `RedisSaver` | `langgraph-checkpoint-redis` | Fast, distributed, high-throughput | `pip install langgraph-checkpoint-redis` |
| `MongoDBSaver` | `langgraph-checkpoint-mongodb` | MongoDB users | `pip install langgraph-checkpoint-mongodb` |

### Thread IDs — How Checkpointing Works

Every invocation of a checkpointed graph requires a `thread_id` in the config:
```python
config = {"configurable": {"thread_id": "run-2026-03-21-WIPRO"}}
result = graph.invoke(state, config=config)
```

State is stored per thread. Different `thread_id` values create independent execution histories. For MMCI, a good thread ID scheme is `{date}_{symbol}_{run_number}`.

### Recommended Checkpointing Strategy for MMCI

| Phase | Checkpointer | Rationale |
|---|---|---|
| Development & Testing | `MemorySaver` | No setup needed, fast iteration |
| Local Production | `SqliteSaver` | Zero infrastructure, survives restarts |
| Production (Phase 2+) | `PostgresSaver` | Queryable history, multi-process safe, production-grade |

**Start with `MemorySaver` for development, then promote to `SqliteSaver` before production use.** The checkpointer is configured at compile time, so switching is one line of code.

### Pending Writes — Critical for Parallel Superstep Recovery

When a parallel superstep partially fails (e.g., 4 of 5 model nodes succeed, 1 fails), LangGraph with a checkpointer stores the **pending writes** (successful node outputs) so that on resume, the 4 successful nodes do NOT re-execute. Only the failed node retries.

This is critical for MMCI: if one LLM API call fails and we retry, we don't want to re-call the other 4 models unnecessarily (wasting rate limit budget).

---

## R4.7 — Async Execution — ainvoke, astream, asyncio

### Sync vs Async — The Core Distinction

LangGraph supports both:
- **Sync:** `graph.invoke(state)` — blocks until complete
- **Async:** `await graph.ainvoke(state)` — non-blocking, uses Python asyncio

For MMCI, async is strongly recommended because:
- 5 model API calls in parallel = up to 30 seconds of I/O wait
- With async, Python can yield control during each API call's wait time
- With sync + threads (via `asyncio.to_thread`), same result but more overhead

### Async Node Functions

Any node function can be declared as async:
```python
async def claude_node(state: PantheonState) -> dict:
    response = await claude_client.ainvoke(state["model_prompts"]["claude"])
    return {"model_signals": [parse_signal(response)]}
```

When nodes are async, LangGraph automatically uses `asyncio.gather()` under the hood for the parallel superstep — meaning all 5 async model nodes execute in true async concurrency.

### Known Gotcha: functools.partial with Async

A documented community-discovered bug: `functools.partial()` does not work correctly with async node functions in LangGraph. The partial application strips the `async` nature of the function.

**Fix for MMCI:** Instead of using `functools.partial` to bind model-specific config to a generic node function, use a factory pattern:

```python
# WRONG — breaks async
node = functools.partial(generic_model_node, model_id=ModelID.CLAUDE)

# CORRECT — preserves async
def make_model_node(model_id: ModelID):
    async def node(state: PantheonState) -> dict:
        # model_id is captured in closure
        return await call_model(model_id, state)
    node.__name__ = f"{model_id.value}_node"
    return node

claude_node = make_model_node(ModelID.CLAUDE)
```

This pattern is already reflected in the MMCI graph design from the earlier coding session. No change needed — the factory `_make_model_node()` function was already correct.

### Using `asyncio.to_thread` for Sync SDK Calls

If a provider SDK only supports sync calls (no `await`), use `asyncio.to_thread` to avoid blocking:
```python
async def groq_node(state: PantheonState) -> dict:
    # groq_client.invoke() is synchronous — wrap it
    response = await asyncio.to_thread(groq_client.invoke, state["model_prompts"]["groq"])
    return {"model_signals": [parse_signal(response)]}
```

### Type-Safe Streaming (LangGraph 1.1 — Optional)

LangGraph 1.1 introduces opt-in typed streaming:
```python
async for chunk in graph.astream(state, version="v2"):
    if chunk["type"] == "values":
        # Access typed state update
        print(chunk["data"])
```

For MMCI, streaming is not needed in Phase 1 (batch analysis). This is a Phase 3 feature for a real-time dashboard.

---

## R4.8 — Error Handling — RetryPolicy, Superstep Atomicity

### The Superstep Atomicity Problem — Critical for MMCI Design

**This is the most important operational constraint to understand.**

When running 5 model nodes in parallel in a single superstep:

- If ALL 5 succeed → state updates are applied, graph continues
- If ANY 1 fails (unhandled exception) → **the ENTIRE superstep fails atomically**
  - None of the 5 updates are applied to the state
  - With checkpointer: successful nodes' outputs are saved as pending writes
  - Without checkpointer: all 5 must retry

**For MMCI this is dangerous:** If Mistral's API is down and throws an exception, it would kill the entire superstep and discard the results from 4 other successful model calls — wasting rate limit budget.

**Solution: Never let a model node throw an uncaught exception.** Every model node must catch all exceptions internally and return a failed `ModelSignal` instead:

```python
async def claude_node(state: PantheonState) -> dict:
    try:
        response = await call_claude(state["model_prompts"]["claude"])
        signal = parse_signal(ModelID.CLAUDE, response)
    except Exception as e:
        signal = ModelSignal(
            model_id=ModelID.CLAUDE,
            direction=Direction.HOLD,
            confidence=0.0,
            timeframe=Timeframe.MEDIUM,
            reasoning="",
            failed=True,
            failure_reason=str(e)
        )
    return {"model_signals": [signal]}
```

This is the MMCI pattern already designed. Confirm it's implemented in all 5 model nodes before any testing.

### RetryPolicy — Graph-Level Retry Configuration

LangGraph provides `RetryPolicy` for graph-managed retries. Configure per-node:

```python
from langgraph.types import RetryPolicy

builder.add_node(
    "claude_node",
    claude_node,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=1.0,
        backoff_factor=2.0,      # 1s, 2s, 4s
        retry_on=lambda e: isinstance(e, (httpx.TimeoutException, httpx.HTTPStatusError))
    )
)
```

**Key details about RetryPolicy:**
- Only **failing branches** are retried, not all nodes
- `retry_on` accepts a callable that filters which exceptions trigger retry
- Default retries on most exceptions; 5xx HTTP codes specifically for HTTP exceptions
- Known bug (GitHub issue #6027, August 2025): `RetryPolicy` does NOT catch `pydantic.ValidationError`. If a model returns malformed JSON that fails Pydantic validation, the retry is skipped. Fix: wrap Pydantic validation in a `try/except` block inside the node instead.

### When Retries Are Exhausted

When a node exhausts all `RetryPolicy` retries, the final exception propagates and the graph stops. If you need to redirect flow to an error-handling node after retries are exhausted, you cannot use `RetryPolicy` for this — you must implement your own retry wrapper inside the node function.

For MMCI, the correct approach is: RetryPolicy handles transient network failures. The node's internal try/except handles permanent failures (returns a failed ModelSignal). No need for post-retry flow redirection.

### recursion_limit — Preventing Infinite Loops

LangGraph has a built-in `recursion_limit` (default: 25) that prevents infinite execution cycles. If your graph has loops (MMCI doesn't in Phase 1), this limit applies.

```python
result = graph.invoke(state, config={"recursion_limit": 50})
```

For MMCI which is a DAG (no cycles), this is irrelevant.

---

## R4.9 — Known Limitations, Bugs & Gotchas

This section compiles all known issues from the community forum, GitHub issues, and production engineering articles — relevant to MMCI's design.

### L1: Parallel superstep updates are non-deterministic

State updates from parallel nodes in the same superstep are applied in an unspecified order. If you need ordering, write to a separate field with an identifying key and sort in the fan-in node.

**MMCI impact:** Medium. The `model_signals` list may have signals appended in any order. The MMCI algorithm must not assume any ordering. Solution: sort by `model_id` in `dissent_check_node` if consistent output is needed for testing/debugging.

### L2: RetryPolicy does not catch pydantic.ValidationError

Confirmed bug (GitHub #6027). When a model returns a malformed response that fails Pydantic validation, RetryPolicy is bypassed.

**MMCI impact:** High. Our structured output parsing uses Pydantic. Fix: wrap ALL Pydantic model_validate calls in try/except inside the node. Already reflected in the architecture.

### L3: functools.partial breaks async nodes

Documented in community forum. Using `functools.partial` to bind parameters to an async node function strips its coroutine nature.

**MMCI impact:** High (if we use partial). Already mitigated by using the factory/closure pattern in `_make_model_node()`.

### L4: langgraph dev command ignores custom checkpointers

GitHub issue #5790 (August 2025). The `langgraph dev` CLI command (for LangGraph Studio) forces in-memory storage and ignores configured checkpointers.

**MMCI impact:** Low. We won't be using LangGraph Studio for production. This only affects local development visualization.

### L5: asyncio.run() inside sync LangGraph node causes deadlock

Using `asyncio.run()` inside a sync node function to call async code causes deadlocks in environments with an existing event loop (e.g., Jupyter, FastAPI).

**MMCI impact:** Medium. If running MMCI from a FastAPI endpoint (Phase 2), use `await graph.ainvoke()` not `asyncio.run(graph.invoke())`. Already planned.

### L6: LangGraph Platform timeout errors (Issue #4620)

When LangGraph Platform (the cloud deployment product) is configured with PostgreSQL and experiences connection timeouts, the entire graph shuts down.

**MMCI impact:** None. We are not using LangGraph Platform. We're self-hosting. This is a cloud platform-specific issue.

### L7: High parallelism (70+ nodes) community concerns

A production user reported issues with 70+ parallel nodes per run (community forum, October 2025). LangGraph's `max_concurrency` parameter was the recommended mitigation.

**MMCI impact:** None. We have only 5 parallel model nodes — well within safe bounds.

### L8: Fan-out can stall if Send target returns incompatible state shape

If using the Send API and a target node returns state that doesn't match what the aggregator node expects, the parallel workflow stalls silently.

**MMCI impact:** Low. We're using static edges, not Send API. But relevant to note for Phase 2.

### L9: Thread-level namespace collision in multi-tenant checkpointing

In a multi-user deployment, if two users' graph runs share the same `thread_id`, their states can be mixed.

**MMCI impact:** None in Phase 1 (single user). Relevant when building the SaaS version — use `{user_id}_{date}_{symbol}` as thread ID pattern.

---

## R4.10 — LangGraph vs LangChain LCEL — Definitive Decision

This question is frequently asked, and the answer directly affects what we import and how we structure MMCI.

### Summary: They Are Complementary, Not Competing

After LangGraph 1.0 (October 2025):
- **LangChain agents now run on LangGraph under the hood** — they are not separate systems
- **LangChain provides:** Model wrappers, prompt templates, output parsers, document loaders, tool abstractions, vector store connectors
- **LangGraph provides:** Stateful execution, parallel fan-out, checkpointing, human-in-the-loop, time-travel debugging, graph topology

The correct mental model: **LangChain components live inside LangGraph nodes.** You use LangChain's `ChatGoogleGenerativeAI`, `ChatOpenAI` etc. objects inside LangGraph node functions.

### For MMCI: Use LangGraph as the Orchestrator, LangChain as the Tool Supplier

```
LangGraph StateGraph (MMCI orchestration layer)
    ├── claude_node (uses langchain_anthropic.ChatAnthropic inside)
    ├── gemini_node (uses langchain_google_genai.ChatGoogleGenerativeAI inside)
    ├── groq_node   (uses langchain_openai.ChatOpenAI with Groq base_url inside)
    ├── ...
    └── dissent_check_node (pure Python — no LangChain needed)
```

LCEL (LangChain Expression Language) is **not needed** for MMCI. LCEL is designed for linear pipelines. Our workflow has parallel branches, conditional routing, and checkpointing — all of which require LangGraph, not LCEL.

### Decision Rule

Use LangChain LCEL when: Sequential, stateless, simple prompt-to-output workflows  
Use LangGraph when: Parallel execution, stateful multi-step workflows, conditional branching, retries at graph level, checkpointing

MMCI is firmly in the LangGraph category. LangChain components are used inside nodes as utilities only.

---

## R4.11 — LangGraph's Direct Applicability to MMCI

This section maps every MMCI requirement to the corresponding LangGraph feature, with a confidence rating that it will work as designed.

### MMCI Requirement → LangGraph Feature Mapping

| MMCI Requirement | LangGraph Feature | Confidence | Notes |
|---|---|---|---|
| Run 5 model API calls simultaneously | Static parallel edges (multiple `add_edge` from one node) | ✅ Confirmed | Core supported feature, well-documented |
| Merge 5 model signals into one list | `operator.add` reducer on `model_signals` state key | ✅ Confirmed | Standard pattern |
| Wait for all models before scoring | Fan-in edge topology + optional `defer=True` | ✅ Confirmed | Works for variable-length branches |
| Route to HOLD on high dissent | `add_conditional_edges` with router function | ✅ Confirmed | Standard conditional edge pattern |
| Persist signal history for T+5 weight update | SQLite checkpointer | ✅ Confirmed | Direct feature |
| Retry failed model calls up to 3 times | `RetryPolicy` with custom `retry_on` | ✅ Confirmed | Watch for Pydantic validation bug (L2) |
| Skip failed models, proceed with remaining | Internal try/except in each model node | ✅ Confirmed | Application-level pattern |
| Run entire graph async | `graph.ainvoke()` with async node functions | ✅ Confirmed | Direct feature |
| Limit to minimum 3 active models | Guard in `dissent_check_node` | ✅ Confirmed | Application-level check in node |
| Schedule T+5 weight update job | External Python scheduler (not LangGraph) | N/A | LangGraph is for the analysis run; weight update is a separate scheduled job |
| Visualize graph execution | LangGraph Studio | ✅ Confirmed | Development tool; separate setup |
| Progressive state build across nodes | `total=False` TypedDict | ✅ Confirmed | Not all keys need to be present initially |

### Execution Flow Verified Against LangGraph Capabilities

The full MMCI graph topology previously designed:
```
START → data_ingestion → prompt_builder → [5 model nodes in parallel] → dissent_check → (conditional) → consensus_scoring → position_sizing → output → END
                                                                                        ↘ hold_output → END
```

This topology is entirely within LangGraph's supported patterns. Every single feature used (parallel edges, conditional routing, fan-in, reducers) is documented and production-proven.

**One adjustment needed from original design:** The `dissent_check_node` should be marked `defer=True` to ensure it waits for ALL model nodes even if some branches have different completion times. This is cleaner than relying purely on edge topology.

---

## R4.12 — Package Ecosystem & Installation Map

### Core Packages

```
langgraph>=1.1.0                   # Core graph execution
langchain>=1.0.3                   # LangChain v1 (stable)
langchain-core>=0.3.x              # Core primitives (auto-installed with langchain)
langchain-google-genai>=2.1.0      # Gemini model wrapper
langchain-openai>=1.1.0            # OpenAI-compatible wrapper (Groq, OpenRouter, Mistral)
pydantic>=2.0.0                    # State validation
```

### Checkpointer Packages (install the one you need)

```
langgraph-checkpoint-sqlite>=3.0.3  # Development and local production
langgraph-checkpoint-postgres>=4.0.0 # Production (install when ready)
```

### Why Only One Model Wrapper Is Needed (OpenAI-Compatible APIs)

**Critical discovery for MMCI's implementation simplicity:**

All of our free tier providers (Groq, OpenRouter, Mistral) expose an OpenAI-compatible API. This means we can use `langchain-openai`'s `ChatOpenAI` for ALL of them by simply changing the `base_url` and `api_key`:

```python
from langchain_openai import ChatOpenAI

# Groq (OpenAI-compatible)
groq_llama = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"]
)

# Mistral (OpenAI-compatible)
mistral = ChatOpenAI(
    model="mistral-small-3.1",
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ["MISTRAL_API_KEY"]
)

# OpenRouter (OpenAI-compatible)
deepseek = ChatOpenAI(
    model="deepseek/deepseek-r1:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

# Only Gemini needs its own wrapper
from langchain_google_genai import ChatGoogleGenerativeAI
gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=os.environ["GEMINI_API_KEY"]
)
```

This means the entire adapter layer for Groq + Mistral + OpenRouter is **one import** (`ChatOpenAI`) and configuration, not separate provider-specific libraries. This significantly reduces the implementation surface area compared to the original design.

---

## R4.13 — Architecture Decision Records (ADRs) for Pantheon

These are the formal decisions made based on R4 research. Each represents a choice that was evaluated and justified.

---

### ADR-001: Use Static Parallel Edges, Not Send API

**Decision:** Use `builder.add_edge()` for all parallel model nodes, not the `Send` API.

**Rationale:**
- The number of parallel model calls (5) is fixed and known at design time
- Static edges are simpler, more debuggable, and more readable
- Send API adds complexity without benefit for our fixed-N use case
- Save Send API for Phase 2 if we need to dynamically select which models run

**Status:** DECIDED ✅

---

### ADR-002: All Model Nodes Must Catch All Exceptions Internally

**Decision:** No model node may propagate an exception to the LangGraph runtime. All failures must be caught and returned as a failed `ModelSignal`.

**Rationale:**
- LangGraph superstep atomicity: one uncaught exception cancels the whole superstep
- Would discard the results of all other model nodes, wasting API rate limit budget
- A failed model is a known, valid state in MMCI (weight penalty applied, excluded from scoring)

**Status:** DECIDED ✅

---

### ADR-003: Use TypedDict with total=False for PantheonState

**Decision:** Use `TypedDict` with `total=False` (no fields required) rather than Pydantic BaseModel for the state schema.

**Rationale:**
- Fields are populated progressively across nodes; TypedDict with total=False reflects this naturally
- Lower overhead than Pydantic on every state transition
- Fully compatible with all LangGraph APIs (no version flags needed)
- LangGraph 1.1 Pydantic coercion is opt-in via version="v2" flag — not needed for Phase 1

**Status:** DECIDED ✅

---

### ADR-004: Use dissent_check_node with defer=True

**Decision:** Mark `dissent_check_node` as `defer=True` in addition to connecting it via fan-in edges.

**Rationale:**
- `defer=True` creates an explicit synchronization barrier
- Ensures correct behavior even if some model branches have multiple internal steps in Phase 2
- Cleaner than relying purely on edge topology for synchronization semantics

**Status:** DECIDED ✅

---

### ADR-005: Start with MemorySaver, Promote to SqliteSaver Before Production

**Decision:** Use `MemorySaver` during development. Switch to `SqliteSaver` before first production run.

**Rationale:**
- MemorySaver requires zero setup for fast development iteration
- SqliteSaver provides persistence that survives restarts with single-file simplicity
- PostgresSaver is reserved for Phase 2 (multi-user, queryable history)
- All three are interchangeable with one line of code change

**Status:** DECIDED ✅

---

### ADR-006: Use langchain-openai as Unified Adapter for Non-Google Providers

**Decision:** Use `ChatOpenAI` from `langchain-openai` with custom `base_url` for Groq, Mistral, and OpenRouter. Use `ChatGoogleGenerativeAI` only for Gemini.

**Rationale:**
- All non-Google providers use OpenAI-compatible API format
- Single import reduces dependency surface area
- Simplifies the model adapter layer significantly
- Switching providers requires only changing base_url and api_key

**Status:** DECIDED ✅

---

## R4.14 — Open Items & Carry-forwards

| Item | Details | Feeds Into |
|---|---|---|
| LangGraph Studio compatibility | Test whether `langgraph dev` works with our custom state schema and checkpointer | Development phase setup |
| Structured output reliability | Evaluate each free-tier model's ability to consistently return structured JSON matching ModelSignal schema | Prompt engineering phase |
| Timeout configuration | Determine appropriate per-model timeout values based on testing free-tier API latency | Data pipeline design |
| asyncio.to_thread necessity per provider | Determine which provider SDKs are sync-only (need `asyncio.to_thread`) vs. native async (can use `await`) | Implementation phase |
| LangGraph vs PydanticAI evaluation | PydanticAI is a newer alternative for typed agent workflows — worth a brief evaluation to confirm LangGraph is the right choice | Architecture phase (brief) |
| LangSmith observability | LangSmith is the official observability/tracing tool for LangGraph. Free tier available. Evaluate whether to integrate for signal audit trail | Phase 2 planning |

---

## Summary — What R4 Confirms for Project Pantheon

| Question | Answer |
|---|---|
| Does LangGraph support the MMCI parallel fan-out pattern? | ✅ Yes, natively. Multiple `add_edge()` calls from one node to multiple nodes. Core documented feature. |
| Does it handle variable-length parallel branches? | ✅ Yes. LangGraph waits for all branches regardless of step count. Use `defer=True` for explicit sync. |
| Is the state reducer pattern stable and well-understood? | ✅ Yes. `Annotated[list, operator.add]` is the standard pattern. Extensively documented and production-proven. |
| Is the current version stable and production-ready? | ✅ Yes. LangGraph 1.0+ commits to no breaking changes until v2.0. Used by Uber, JP Morgan, Blackrock. |
| Does async execution work for LLM API calls? | ✅ Yes. Use `async def` nodes + `graph.ainvoke()`. 5 parallel API calls run concurrently via asyncio. |
| Is the RetryPolicy reliable? | ⚠️ Mostly. Known bug: doesn't catch `pydantic.ValidationError`. Mitigate by wrapping Pydantic calls in try/except. |
| Does LangGraph handle partial parallel failures gracefully? | ✅ Yes, with a checkpointer. Without checkpointer: entire superstep retries. With checkpointer: only failed nodes retry. |
| Are there any known issues blocking MMCI's design? | ✅ No blocking issues. All issues have known workarounds that are already in the MMCI design. |

---

*End of Document — R4: LangGraph Architecture Research*  
*Next: R5 — Prior Art Survey (existing LLM-based trading systems, what MMCI adds that doesn't already exist, novelty claim formulation for the research paper)*
