from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.cache.memory import InMemoryCache
from agents.state import PantheonState
from extractors import get_all_extractors
from extractors.prompts import build_all_prompts
from mmci.scoring import (compute_dissent_score, compute_consensus_score,
                           determine_direction, compute_position_size,
                           compute_risk_level, synthesize_reasoning,
                           determine_consensus_timeframe)
from mmci.weights import WeightManager, INITIAL_WEIGHTS
from mmci.models import ModelID, Direction, MarketRegime
from data.weights_store import load_weights
from config.settings import settings
import asyncio
import uuid
from datetime import datetime
import statistics
from collections import Counter
import time
from extractors.base import ModelSignal

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
    signals = state.get("model_signals", [])
    active = [s for s in signals if not s.get("failed", False)]
    
    if len(active) < settings.MIN_MODELS_REQUIRED:
        return {
            "dissent_score": 0.0, 
            "dissent_flag": True,
            "errors": ["INSUFFICIENT_SIGNALS"]
        }
        
    signed = []
    for s in active:
        d_val = 1 if s["direction"] == "BUY" else (-1 if s["direction"] == "SELL" else 0)
        signed.append(s["confidence"] * d_val)
        
    D = statistics.variance(signed) if len(signed) > 1 else 0.0
    return {
        "dissent_score": round(D, 6),
        "dissent_flag": D > settings.DISSENT_THRESHOLD
    }

def consensus_scoring_node(state: dict):
    weights = load_weights()
    signals = [s for s in state.get("model_signals", []) if not s.get("failed", False)]
    
    weighted_sum = 0.0
    total_w = 0.0
    
    for s in signals:
        w = weights.get(s["model_id"], 0.17)
        d_val = 1 if s["direction"] == "BUY" else (-1 if s["direction"] == "SELL" else 0)
        weighted_sum += w * s["confidence"] * d_val
        total_w += w
        
    S = weighted_sum / total_w if total_w > 0 else 0.0
    regime = state.get("market_regime", "SIDEWAYS")
    
    thresholds = {
        "BULL":     {"buy": 0.20, "sell": -0.45},
        "SIDEWAYS": {"buy": 0.30, "sell": -0.30},
        "BEAR":     {"buy": 0.45, "sell": -0.20},
    }
    t = thresholds.get(regime, thresholds["SIDEWAYS"])
    
    if S > t["buy"]:   
        direction = "BUY"
    elif S < t["sell"]: 
        direction = "SELL"
    else:               
        direction = "HOLD"
        
    return {"consensus_score": round(S, 6), "final_direction": direction}

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
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {"final_signal": final}

def route_after_dissent(state: dict):
    return "hold_output_node" if state.get("dissent_flag") else "consensus_scoring_node"

def build_graph():
    builder = StateGraph(PantheonState)
    builder.add_node("prompt_builder_node", prompt_builder_node)
    
    extractors = get_all_extractors()
    model_nodes = []
    
    for extractor in extractors:
        node_func = make_model_node(extractor)
        builder.add_node(node_func.__name__, node_func)
        model_nodes.append(node_func.__name__)
        
    builder.add_node("dissent_check_node", dissent_check_node)
    builder.add_node("consensus_scoring_node", consensus_scoring_node)
    builder.add_node("position_sizing_node", position_sizing_node)
    builder.add_node("output_node", output_node)
    builder.add_node("hold_output_node", hold_output_node)
    
    builder.add_edge(START, "prompt_builder_node")
    
    for name in model_nodes:
        builder.add_edge("prompt_builder_node", name)
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
    
    return builder.compile()
