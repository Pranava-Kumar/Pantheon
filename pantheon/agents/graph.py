from langgraph.graph import StateGraph, START, END
from pantheon.agents.state import PantheonState
from pantheon.extractors import get_all_extractors
from pantheon.extractors.prompts import build_all_prompts
from pantheon.mmci.scoring import (compute_dissent_score, compute_consensus_score,
                           compute_sentiment_score, compute_technical_score,
                           compute_fundamental_score, compute_total_mmci_score,
                           determine_direction, compute_position_size,
                           compute_risk_level)
from pantheon.mmci.weights import WeightManager, INITIAL_WEIGHTS, INITIAL_CATEGORY_WEIGHTS
from pantheon.mmci.models import ModelID, Direction, MarketRegime
from pantheon.data.weights_store import load_weights
from pantheon.config.settings import settings
import asyncio
import uuid
from datetime import datetime, timezone
from collections import Counter
import time
from pantheon.extractors.base import ModelSignal

def prompt_builder_node(state: dict):
    prompts = build_all_prompts(state.get("stock_context", {}))
    return {"model_prompts": prompts}

def make_model_node(extractor):
    async def node(state: dict):
        try:
            prompt = state.get("model_prompts", {}).get(extractor.model_id, "")
            signal = await extractor.extract(prompt)
        except Exception as e:
            start_time = time.monotonic()
            signal = ModelSignal(
                model_id=extractor.model_id,
                direction="HOLD",
                confidence=0.0,
                timeframe="MEDIUM",
                reasoning="",
                failed=True,
                failure_reason=str(e)[:200],
                latency_ms=int((time.monotonic() - start_time) * 1000)
            )
        return {"model_signals": [signal.to_dict()]}
    node.__name__ = f"{extractor.model_id}_node"
    return node

def dissent_check_node(state: dict):
    """
    Check for dissent among model signals using the standardized dissent score.
    
    Uses compute_dissent_score from scoring.py which implements a weighted
    disagreement ratio rather than raw variance for more accurate dissent detection.
    
    Args:
        state: Current graph state with model_signals.
        
    Returns:
        Dictionary with dissent_score and dissent_flag.
    """
    signals = state.get("model_signals", [])
    active = [s for s in signals if not s.get("failed", False)]

    if len(active) < settings.MIN_MODELS_REQUIRED:
        return {
            "dissent_score": 0.0,
            "dissent_flag": True,
            "errors": ["INSUFFICIENT_SIGNALS"]
        }

    # Use standardized dissent score from scoring.py (not variance)
    D = compute_dissent_score(signals)
    return {
        "dissent_score": D,
        "dissent_flag": D > settings.DISSENT_THRESHOLD
    }

def consensus_scoring_node(state: dict):
    # 1. Load weights
    wm = WeightManager()
    model_weights = wm.get_weights()
    category_weights = wm.get_category_weights()
    
    # 2. Extract signals and context
    signals = state.get("model_signals", [])
    ctx = state.get("stock_context", {})
    regime = state.get("market_regime", "SIDEWAYS")
    
    # 3. Compute category scores
    # Sentiment score from LLM model consensus
    sentiment_score = compute_consensus_score(signals, model_weights)
    
    # Technical score from raw indicators
    tech_indicators = ctx.get("technicals", {})
    tech_score = compute_technical_score(tech_indicators)
    
    # Fundamental score from fundamental data
    fund_data = ctx.get("fundamentals", {})
    fund_score = compute_fundamental_score(fund_data)
    
    # 4. Compute Total MMCI Score (Weighted aggregation)
    total_score = compute_total_mmci_score(
        tech_score, 
        fund_score, 
        sentiment_score, 
        category_weights
    )
    
    # 5. Determine direction based on regime thresholds
    direction = determine_direction(total_score, regime)
    
    return {
        "consensus_score": total_score,
        "sentiment_score": sentiment_score, 
        "final_direction": direction
    }

def position_sizing_node(state: dict):
    S = state["consensus_score"]
    D = state["dissent_score"]
    
    alloc = abs(S) * settings.MAX_ALLOC * max(0.0, 1.0 - D)
    alloc = round(min(alloc, settings.MAX_ALLOC), 4)
    
    regime = state.get("market_regime", "SIDEWAYS")
    base = {"BULL": 1, "SIDEWAYS": 2, "BEAR": 3}.get(regime, 2)
    risk = min(5, max(1, base + int((1 - abs(S)) * 2)))
    
    return {"suggested_alloc": alloc, "risk_level": risk}

def output_node(state: dict):
    signals = state.get("model_signals", [])
    active = [s for s in signals if not s.get("failed", False)]
    directions = [s["direction"] for s in active]

    if directions:
        timeframe = Counter(s["timeframe"] for s in active).most_common(1)[0][0]
    else:
        timeframe = "MEDIUM"

    final = {
        "run_id": str(state.get("run_id", uuid.uuid4())),
        "symbol": state.get("symbol", ""),
        "direction": state["final_direction"],
        "consensus_score": state["consensus_score"],
        "dissent_score": state["dissent_score"],
        "dissent_flag": False,
        "market_regime": state.get("market_regime", "SIDEWAYS"),
        "timeframe": timeframe,
        "suggested_alloc": state["suggested_alloc"],
        "risk_level": state["risk_level"],
        "model_signals": signals,
        "models_used": len(active),
        "reasoning": f"{state['final_direction']} signal. Consensus S={state['consensus_score']:.3f}, D={state['dissent_score']:.3f}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return {"final_signal": final}

def hold_output_node(state: dict):
    signals = state.get("model_signals", [])
    active = [s for s in signals if not s.get("failed", False)]
    directions = [s["direction"] for s in active]

    if directions:
        timeframe = Counter(s["timeframe"] for s in active).most_common(1)[0][0]
    else:
        timeframe = "MEDIUM"

    final = {
        "run_id": str(state.get("run_id", uuid.uuid4())),
        "symbol": state.get("symbol", ""),
        "direction": "HOLD",
        "consensus_score": 0.0,
        "dissent_score": state.get("dissent_score", 0.0),
        "dissent_flag": True,
        "market_regime": state.get("market_regime", "SIDEWAYS"),
        "timeframe": timeframe,
        "suggested_alloc": 0.0,
        "risk_level": 4,
        "model_signals": signals,
        "models_used": len(active),
        "reasoning": f"DISSENT or INSUFFICIENT SIGNALS. D={state.get('dissent_score', 0.0):.3f}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return {"final_signal": final}

def route_after_dissent(state: dict):
    return "hold_output_node" if state.get("dissent_flag") else "consensus_scoring_node"

async def batch_separator_node(state: dict):
    """
    Introduces a small delay between model batches to mitigate shared rate limit pressure.
    
    This node runs after Groq models complete and before Gemini models start,
    ensuring we don't exceed API rate limits when using multiple providers.
    
    Args:
        state: Current graph state dictionary.
        
    Returns:
        Empty dictionary (state passthrough).
    """
    await asyncio.sleep(settings.BATCH_SEPARATOR_DELAY_SECONDS)
    return {}

def build_graph():
    builder = StateGraph(PantheonState)
    builder.add_node("prompt_builder_node", prompt_builder_node)
    builder.add_node("batch_separator_node", batch_separator_node)

    extractors = get_all_extractors()
    groq_nodes = []
    gemini_nodes = []

    for extractor in extractors:
        node_func = make_model_node(extractor)
        builder.add_node(node_func.__name__, node_func)
        if "groq" in extractor.model_id:
            groq_nodes.append(node_func.__name__)
        else:
            gemini_nodes.append(node_func.__name__)

    builder.add_node("dissent_check_node", dissent_check_node)
    builder.add_node("consensus_scoring_node", consensus_scoring_node)
    builder.add_node("position_sizing_node", position_sizing_node)
    builder.add_node("output_node", output_node)
    builder.add_node("hold_output_node", hold_output_node)

    # Execution Flow:
    # 1. Build Prompts
    builder.add_edge(START, "prompt_builder_node")

    # 2. Run Groq Models first
    for name in groq_nodes:
        builder.add_edge("prompt_builder_node", name)
        builder.add_edge(name, "batch_separator_node")

    # 3. Run Gemini Models last
    for name in gemini_nodes:
        builder.add_edge("batch_separator_node", name)
        builder.add_edge(name, "dissent_check_node")

    builder.add_conditional_edges(
        "dissent_check_node",
        route_after_dissent,
        {
            "hold_output_node": "hold_output_node",
            "consensus_scoring_node": "consensus_scoring_node"
        }
    )

    builder.add_edge("consensus_scoring_node", "position_sizing_node")
    builder.add_edge("position_sizing_node", "output_node")
    builder.add_edge("output_node", END)
    builder.add_edge("hold_output_node", END)

    # Compile without checkpointer - each analysis is stateless and independent
    # MemorySaver is not needed for stateless daily stock analysis
    return builder.compile()
