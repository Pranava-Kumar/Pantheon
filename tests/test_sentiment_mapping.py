import pytest
from pantheon.mmci.scoring import compute_sentiment_score

def test_compute_sentiment_score_positive():
    # Mock news signals (direction, confidence)
    signals = [
        {"model_id": "gemini_flash", "direction": "BUY", "confidence": 0.8},
        {"model_id": "gemini_pro", "direction": "BUY", "confidence": 0.6},
    ]
    score = compute_sentiment_score(signals)
    assert score > 0.5

def test_compute_sentiment_score_negative():
    signals = [
        {"model_id": "gemini_flash", "direction": "SELL", "confidence": 0.9},
        {"model_id": "gemini_pro", "direction": "HOLD", "confidence": 0.5},
    ]
    score = compute_sentiment_score(signals)
    assert score < -0.2

def test_compute_sentiment_score_neutral():
    signals = [
        {"model_id": "gemini_flash", "direction": "HOLD", "confidence": 0.5},
    ]
    score = compute_sentiment_score(signals)
    assert score == 0.0
