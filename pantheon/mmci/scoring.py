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

from .weights import INITIAL_WEIGHTS, INITIAL_CATEGORY_WEIGHTS

def compute_technical_score(indicators: dict) -> float:
    """
    Maps raw technical indicators to a sentiment score (-1.0 to 1.0).
    """
    score = 0.0
    count = 0
    
    # RSI: >70 is bearish (overbought), <30 is bullish (oversold)
    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi > 70: score -= 0.5
        elif rsi < 30: score += 0.5
        count += 1
        
    # MACD: Positive hist is bullish
    macd_hist = indicators.get("macd_hist")
    if macd_hist is not None:
        if macd_hist > 0: score += 0.3
        else: score -= 0.3
        count += 1
        
    # EMA: Price above EMA 50 is bullish
    # This requires price which might not be in the indicators dict directly
    # but we can assume it's passed or focus on what we have.
    
    return round(max(-1.0, min(1.0, score)), 6) if count > 0 else 0.0

def compute_fundamental_score(data: dict) -> float:
    """
    Maps fundamental data to a sentiment score (-1.0 to 1.0).
    """
    score = 0.0
    count = 0
    
    # Simple example logic
    roe = data.get("roe")
    if roe is not None:
        if roe > 15: score += 0.4
        elif roe < 8: score -= 0.4
        count += 1
        
    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 10: score += 0.4
        elif rev_growth < 0: score -= 0.4
        count += 1
        
    return round(max(-1.0, min(1.0, score)), 6) if count > 0 else 0.0

def compute_total_mmci_score(technical_score: float, 
                             fundamental_score: float, 
                             sentiment_score: float, 
                             category_weights: dict = None) -> float:
    """
    Computes a weighted total score across Technicals, Fundamentals, and Sentiment.
    """
    weights = category_weights or INITIAL_CATEGORY_WEIGHTS
    
    # We use .get(..., 0.0) for safety if the key is missing
    w_tech = weights.get("technicals", 0.40)
    w_fund = weights.get("fundamentals", 0.30)
    w_sent = weights.get("sentiment", 0.30)
    
    total_score = (technical_score * w_tech) + \
                  (fundamental_score * w_fund) + \
                  (sentiment_score * w_sent)
                  
    return round(total_score, 6)

def compute_consensus_score(signals: list[dict], weights: dict = None) -> float:
    active = [s for s in signals if not s.get("failed", False)]
    if not active: return 0.0
    
    weights = weights or INITIAL_WEIGHTS
    weighted_sum = sum(
        weights.get(s["model_id"], 0.20) *
        s["confidence"] *
        (1 if s["direction"]=="BUY" else -1 if s["direction"]=="SELL" else 0)
        for s in active)
    total_w = sum(weights.get(s["model_id"], 0.20) for s in active)
    return round(weighted_sum / total_w, 6) if total_w > 0 else 0.0

def compute_sentiment_score(signals: list[dict]) -> float:
    """
    Computes a sentiment score (-1.0 to 1.0) based on model signals.
    Focuses on models that are sentiment-aware (gemini_flash, gemini_pro, groq_gpt).
    """
    sentiment_models = {"gemini_flash", "gemini_pro", "groq_gpt"}
    active = [s for s in signals if not s.get("failed", False) and s["model_id"] in sentiment_models]
    
    if not active:
        return 0.0
        
    weighted_sum = 0.0
    count = 0
    for s in active:
        d_val = 1 if s["direction"] == "BUY" else (-1 if s["direction"] == "SELL" else 0)
        # We give higher weight to gemini_flash for short-term sentiment/news
        m_weight = 1.5 if s["model_id"] == "gemini_flash" else 1.0
        weighted_sum += d_val * s["confidence"] * m_weight
        count += m_weight
        
    return round(weighted_sum / count, 6) if count > 0 else 0.0

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
