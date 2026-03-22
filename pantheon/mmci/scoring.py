import statistics
import math

DISSENT_THRESHOLD = 0.15

REGIME_THRESHOLDS = {
  "BULL":     {"buy": 0.20, "sell": -0.45},
  "SIDEWAYS": {"buy": 0.30, "sell": -0.30},
  "BEAR":     {"buy": 0.45, "sell": -0.20},
}

def compute_dissent_score(signals: list[dict]) -> float:
    active = [s for s in signals if not s.get("failed", False)]
    if len(active) < 2: return 0.0
    signed = [s["confidence"] * (1 if s["direction"]=="BUY" else -1 if s["direction"]=="SELL" else 0) for s in active]
    return statistics.variance(signed)

def compute_consensus_score(signals: list[dict], weights: dict) -> float:
    active = [s for s in signals if not s.get("failed", False)]
    if not active: return 0.0
    weighted_sum = sum(
        weights.get(s["model_id"], 0.20) *
        s["confidence"] *
        (1 if s["direction"]=="BUY" else -1 if s["direction"]=="SELL" else 0)
        for s in active)
    total_w = sum(weights.get(s["model_id"], 0.20) for s in active)
    return round(weighted_sum / total_w, 6) if total_w > 0 else 0.0

def determine_direction(S: float, regime: str) -> str:
    t = REGIME_THRESHOLDS.get(regime, REGIME_THRESHOLDS["SIDEWAYS"])
    if S > t["buy"]: return "BUY"
    elif S < t["sell"]: return "SELL"
    return "HOLD"

def compute_position_size(S: float, D: float, max_alloc: float = 0.20) -> float:
    return round(min(abs(S) * max_alloc * max(0.0, 1.0 - D), max_alloc), 4)

def compute_risk_level(S: float, D: float, regime: str) -> int:
    base = {"BULL": 1, "SIDEWAYS": 2, "BEAR": 3}.get(regime, 2)
    return min(5, max(1, base + int((1.0 - abs(S)) * 2) + int(D / 0.1)))

# Dummy functions for agents/graph.py backwards compatibility
def synthesize_reasoning(signals: list[dict], final_direction: str) -> str:
    return ""

def determine_consensus_timeframe(signals: list[dict]) -> str:
    return "MEDIUM"
