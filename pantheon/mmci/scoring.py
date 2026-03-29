"""
MMCI scoring functions for computing consensus, dissent, and category scores.
"""

from pantheon.mmci.weights import INITIAL_WEIGHTS, INITIAL_CATEGORY_WEIGHTS

DISSENT_THRESHOLD = 0.15

REGIME_THRESHOLDS = {
    "BULL":     {"buy": 0.20, "sell": -0.45},
    "SIDEWAYS": {"buy": 0.30, "sell": -0.30},
    "BEAR":     {"buy": 0.45, "sell": -0.20},
}

def compute_dissent_score(signals: list[dict]) -> float:
    """
    Computes a dissent score based on directional disagreement among models.

    Uses a standardized disagreement ratio that accounts for both direction
    and confidence, rather than raw variance which can be misleading.
    
    Note: Unanimous HOLD signals are treated as high dissent (uncertainty)
    rather than agreement, since HOLD typically indicates model uncertainty.

    Args:
        signals: List of model signal dictionaries with direction and confidence.

    Returns:
        float: Dissent score between 0.0 (full agreement) and 1.0 (full disagreement).
    """
    active = [s for s in signals if not s.get("failed", False)]
    if len(active) < 2:
        return 0.0

    # Count signals by direction
    buy_signals = [s for s in active if s["direction"] == "BUY"]
    sell_signals = [s for s in active if s["direction"] == "SELL"]
    hold_signals = [s for s in active if s["direction"] == "HOLD"]

    # Unanimous HOLD indicates uncertainty - treat as high dissent
    if len(hold_signals) == len(active):
        return 1.0
    
    # If all signals agree on BUY or SELL, dissent is 0
    if len(buy_signals) == len(active) or len(sell_signals) == len(active):
        return 0.0

    # Calculate weighted disagreement: sum of confidence for minority directions
    direction_counts = {
        "BUY": len(buy_signals),
        "SELL": len(sell_signals),
        "HOLD": len(hold_signals)
    }
    majority_direction = max(direction_counts, key=direction_counts.get)

    # Sum confidence of signals NOT in majority direction
    minority_confidence = sum(
        s["confidence"] for s in active
        if s["direction"] != majority_direction
    )

    # Normalize by total confidence to get 0-1 dissent score
    total_confidence = sum(s["confidence"] for s in active)

    if total_confidence == 0:
        return 0.0

    dissent = minority_confidence / total_confidence
    return round(dissent, 6)


def compute_technical_score(indicators: dict) -> float:
    """
    Maps raw technical indicators to a sentiment score (-1.0 to 1.0).
    
    Args:
        indicators: A dictionary of technical indicator values (e.g., rsi_14, macd_hist).
        
    Returns:
        A float representing the aggregate technical sentiment from -1.0 to 1.0.
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
    
    Uses a comprehensive set of fundamental metrics to evaluate company health:
    - Profitability: ROE, ROCE
    - Growth: Revenue growth, Profit growth
    - Leverage: Debt to equity
    - Valuation: PE ratio, PB ratio
    - Ownership: Promoter holding, FII/DII holding
    
    Args:
        data: A dictionary containing fundamental metrics.
            Required (any): roe, roce, revenue_growth, profit_growth,
                           debt_to_equity, pe_ratio, pb_ratio,
                           promoter_pct, fii_pct, dii_pct

    Returns:
        A float representing the aggregate fundamental sentiment from -1.0 to 1.0.
    """
    score = 0.0
    count = 0
    
    # Profitability Metrics (40% weight total)
    # ROE: Return on Equity - measures profitability relative to shareholder equity
    roe = data.get("roe")
    if roe is not None:
        if roe > 20: score += 0.25  # Excellent
        elif roe > 15: score += 0.20  # Good
        elif roe > 10: score += 0.10  # Average
        elif roe < 5: score -= 0.20  # Poor
        count += 1
    
    # ROCE: Return on Capital Employed - measures efficiency of capital use
    roce = data.get("roce")
    if roce is not None:
        if roce > 20: score += 0.20  # Excellent
        elif roce > 15: score += 0.15  # Good
        elif roce > 10: score += 0.08  # Average
        elif roce < 5: score -= 0.15  # Poor
        count += 1
    
    # Growth Metrics (25% weight total)
    # Revenue Growth - top-line growth
    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 20: score += 0.15  # Excellent growth
        elif rev_growth > 10: score += 0.10  # Good growth
        elif rev_growth > 5: score += 0.05  # Moderate growth
        elif rev_growth < 0: score -= 0.15  # Declining
        count += 1
    
    # Profit Growth - bottom-line growth
    profit_growth = data.get("profit_growth")
    if profit_growth is not None:
        if profit_growth > 20: score += 0.15  # Excellent
        elif profit_growth > 10: score += 0.10  # Good
        elif profit_growth > 5: score += 0.05  # Moderate
        elif profit_growth < 0: score -= 0.15  # Declining
        count += 1
    
    # Leverage Metrics (15% weight)
    # Debt to Equity - financial leverage risk
    debt_to_equity = data.get("debt_to_equity")
    if debt_to_equity is not None:
        if debt_to_equity < 0.3: score += 0.15  # Very low debt
        elif debt_to_equity < 0.5: score += 0.10  # Low debt
        elif debt_to_equity < 1.0: score += 0.05  # Moderate debt
        elif debt_to_equity > 2.0: score -= 0.15  # High debt risk
        count += 1
    
    # Valuation Metrics (10% weight total)
    # PE Ratio - price to earnings (lower is generally better for value)
    pe_ratio = data.get("pe_ratio")
    if pe_ratio is not None:
        if 10 < pe_ratio < 20: score += 0.08  # Reasonable valuation
        elif pe_ratio < 10: score += 0.05  # Potentially undervalued
        elif pe_ratio > 40: score -= 0.10  # Potentially overvalued
        count += 1
    
    # PB Ratio - price to book
    pb_ratio = data.get("pb_ratio")
    if pb_ratio is not None:
        if 1 < pb_ratio < 3: score += 0.07  # Reasonable
        elif pb_ratio < 1: score += 0.05  # Potentially undervalued
        elif pb_ratio > 5: score -= 0.08  # Expensive
        count += 1
    
    # Ownership Metrics (10% weight total)
    # Promoter Holding - high promoter stake aligns interests
    promoter_pct = data.get("promoter_pct")
    if promoter_pct is not None:
        if promoter_pct > 60: score += 0.08  # High promoter confidence
        elif promoter_pct > 40: score += 0.05  # Moderate
        elif promoter_pct < 20: score -= 0.08  # Low promoter stake
        count += 1
    
    # FII/DII Holding - institutional confidence
    fii_pct = data.get("fii_pct")
    dii_pct = data.get("dii_pct")
    institutional = (fii_pct or 0) + (dii_pct or 0)
    if institutional > 0:
        if institutional > 40: score += 0.07  # High institutional interest
        elif institutional > 25: score += 0.04  # Moderate
        elif institutional < 10: score -= 0.05  # Low institutional interest
        count += 1
    
    # Normalize score to -1.0 to 1.0 range
    return round(max(-1.0, min(1.0, score)), 6) if count > 0 else 0.0

def compute_total_mmci_score(technical_score: float,
                             fundamental_score: float,
                             sentiment_score: float,
                             category_weights: dict = None) -> float:
    """
    Computes a weighted total score across Technicals, Fundamentals, and Sentiment.
    
    Args:
        technical_score: Technical analysis score (-1.0 to 1.0).
        fundamental_score: Fundamental analysis score (-1.0 to 1.0).
        sentiment_score: Sentiment analysis score (-1.0 to 1.0).
        category_weights: Optional dict with weights for each category.
            Defaults to INITIAL_CATEGORY_WEIGHTS if not provided.
            
    Returns:
        float: Weighted total MMCI score (-1.0 to 1.0).
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
    """
    Compute weighted consensus score from model signals.
    
    Args:
        signals: List of model signal dictionaries with direction and confidence.
        weights: Optional model weights dict (default: INITIAL_WEIGHTS).
        
    Returns:
        float: Weighted consensus score (-1.0 to 1.0).
    """
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
    Higher weight is given to gemini_flash for short-term sentiment/news analysis.
    
    Args:
        signals: List of model signal dictionaries with direction and confidence.
        
    Returns:
        float: Weighted sentiment score (-1.0 to 1.0).
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
    """
    Determine trading direction (BUY/SELL/HOLD) based on MMCI score and market regime.
    
    Args:
        S: Total MMCI score (-1.0 to 1.0).
        regime: Current market regime (BULL/BEAR/SIDEWAYS).
        
    Returns:
        str: Trading direction - "BUY", "SELL", or "HOLD".
    """
    t = REGIME_THRESHOLDS.get(regime, REGIME_THRESHOLDS["SIDEWAYS"])
    if S > t["buy"]: return "BUY"
    elif S < t["sell"]: return "SELL"
    return "HOLD"

def compute_position_size(S: float, D: float, max_alloc: float = 0.20) -> float:
    """
    Compute suggested position size based on consensus score and dissent.
    
    Args:
        S: Total MMCI score (-1.0 to 1.0).
        D: Dissent score (0.0 to 1.0).
        max_alloc: Maximum allocation per position (default: 0.20 = 20%).
        
    Returns:
        float: Suggested allocation (0.0 to max_alloc).
    """
    return round(min(abs(S) * max_alloc * max(0.0, 1.0 - D), max_alloc), 4)

def compute_risk_level(S: float, D: float, regime: str) -> int:
    """
    Compute risk level (1-5) based on score, dissent, and market regime.
    
    Args:
        S: Total MMCI score (-1.0 to 1.0).
        D: Dissent score (0.0 to 1.0).
        regime: Current market regime (BULL/BEAR/SIDEWAYS).
        
    Returns:
        int: Risk level from 1 (lowest) to 5 (highest).
    """
    base = {"BULL": 1, "SIDEWAYS": 2, "BEAR": 3}.get(regime, 2)
    return min(5, max(1, base + int((1.0 - abs(S)) * 2) + int(D / 0.1)))
