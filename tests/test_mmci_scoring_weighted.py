import pytest
from pantheon.mmci.scoring import (
    compute_total_mmci_score, 
    compute_technical_score, 
    compute_fundamental_score,
    compute_sentiment_score,
    determine_direction,
    compute_position_size,
    compute_risk_level,
    compute_dissent_score
)

def test_compute_sentiment_score():
    signals = [
        {"model_id": "gemini_pro", "direction": "BUY", "confidence": 0.8},
        {"model_id": "gemini_flash", "direction": "SELL", "confidence": 0.4}, # weighted higher
        {"model_id": "groq_qwen", "direction": "BUY", "confidence": 0.9}, # not a sentiment model
    ]
    # gemini_pro: 1 * 0.8 * 1.0 = 0.8
    # gemini_flash: -1 * 0.4 * 1.5 = -0.6
    # weighted_sum = 0.8 - 0.6 = 0.2
    # count = 1.0 + 1.5 = 2.5
    # score = 0.2 / 2.5 = 0.08
    score = compute_sentiment_score(signals)
    assert score == 0.08

def test_determine_direction_bull():
    assert determine_direction(0.5, "BULL") == "BUY"
    assert determine_direction(-0.5, "BULL") == "SELL"
    assert determine_direction(0.1, "BULL") == "HOLD"

def test_compute_position_size():
    # S=0.5, D=0.1, max_alloc=0.20
    # min(0.5 * 0.20 * (1.0 - 0.1), 0.20) = min(0.09, 0.20) = 0.09
    size = compute_position_size(0.5, 0.1, 0.20)
    assert size == 0.09

def test_compute_risk_level():
    # S=0.8, D=0.0, regime=BULL
    # base = 1
    # risk = min(5, max(1, 1 + int((1.0 - 0.8)*2) + int(0.0/0.1)))
    #      = min(5, max(1, 1 + 0 + 0)) = 1
    risk = compute_risk_level(0.8, 0.0, "BULL")
    assert risk == 1

def test_compute_dissent_score():
    signals = [
        {"model_id": "a", "direction": "BUY", "confidence": 1.0},
        {"model_id": "b", "direction": "SELL", "confidence": 1.0},
    ]
    # New implementation: normalized disagreement ratio
    # 1 BUY, 1 SELL = 50% split -> dissent = 0.5
    score = compute_dissent_score(signals)
    assert score == 0.5

def test_compute_technical_score_bullish():
    indicators = {
        "rsi_14": 25,  # Bullish
        "macd_hist": 0.5 # Bullish
    }
    # Expected = 0.5 + 0.3 = 0.8
    score = compute_technical_score(indicators)
    assert score == 0.8

def test_compute_technical_score_bearish():
    indicators = {
        "rsi_14": 75,   # Bearish
        "macd_hist": -0.2 # Bearish
    }
    # Expected = -0.5 - 0.3 = -0.8
    score = compute_technical_score(indicators)
    assert score == -0.8

def test_compute_fundamental_score_strong():
    data = {
        "roe": 20,              # Bullish (+0.4)
        "revenue_growth": 15    # Bullish (+0.4)
    }
    score = compute_fundamental_score(data)
    assert score == 0.8

def test_compute_fundamental_score_weak():
    data = {
        "roe": 5,               # Bearish (-0.4)
        "revenue_growth": -5    # Bearish (-0.4)
    }
    score = compute_fundamental_score(data)
    assert score == -0.8

def test_compute_total_mmci_score_balanced():
    category_weights = {
        "technicals": 0.40,
        "fundamentals": 0.30,
        "sentiment": 0.30
    }
    # tech: 0.5, fund: 0.8, sent: -0.2
    # Weighted = (0.5 * 0.4) + (0.8 * 0.3) + (-0.2 * 0.3)
    #          = 0.20 + 0.24 - 0.06 = 0.38
    score = compute_total_mmci_score(0.5, 0.8, -0.2, category_weights)
    assert score == 0.38

def test_compute_total_mmci_score_default_weights():
    # This should use INITIAL_CATEGORY_WEIGHTS from weights.py
    # tech: 1.0, fund: 0.0, sent: 0.0
    # Expected = 1.0 * 0.4 = 0.4
    score = compute_total_mmci_score(1.0, 0.0, 0.0)
    assert score == 0.4

def test_compute_total_mmci_score_incomplete_data():
    # If some categories are zero or missing, it should still calculate based on what's available
    # tech: 0.0, fund: 0.0, sent: 0.0
    score = compute_total_mmci_score(0.0, 0.0, 0.0)
    assert score == 0.0

def test_compute_technical_score_empty():
    assert compute_technical_score({}) == 0.0

def test_compute_fundamental_score_empty():
    assert compute_fundamental_score({}) == 0.0

def test_compute_sentiment_score_empty():
    assert compute_sentiment_score([]) == 0.0
