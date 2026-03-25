import pytest
import pandas as pd
from pantheon.mmci.scoring import (
    compute_technical_score,
    compute_fundamental_score,
    compute_sentiment_score,
    compute_total_mmci_score
)
from pantheon.data.indicators import compute_indicators

def test_full_mmci_pipeline_logic():
    # 1. Mock Price Data
    df = pd.DataFrame({
        "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
        "high": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115],
        "low": [99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113],
        "volume": [1000] * 15
    })
    
    # 2. Compute Technical Indicators
    indicators = compute_indicators(df)
    assert indicators["rsi_14"] is not None
    
    # 3. Score Technicals
    tech_score = compute_technical_score(indicators)
    
    # 4. Mock Fundamental Data
    fund_data = {
        "roe": 18.0,
        "revenue_growth": 12.0
    }
    fund_score = compute_fundamental_score(fund_data)
    assert fund_score == 0.8 # Based on our scoring.py logic (15% ROE -> 0.4, 10% Growth -> 0.4)
    
    # 5. Mock Sentiment Signals
    signals = [
        {"model_id": "gemini_pro", "direction": "BUY", "confidence": 0.9},
        {"model_id": "gemini_flash", "direction": "BUY", "confidence": 0.8},
    ]
    sent_score = compute_sentiment_score(signals)
    
    # 6. Compute Total MMCI Score
    total_score = compute_total_mmci_score(tech_score, fund_score, sent_score)
    
    # Final check: total_score should be a weighted average
    # With default weights: 0.4*tech + 0.3*fund + 0.3*sent
    expected = (tech_score * 0.4) + (fund_score * 0.3) + (sent_score * 0.3)
    assert total_score == pytest.approx(expected, abs=1e-5)
    print(f"Integration Test Success: Tech={tech_score}, Fund={fund_score}, Sent={sent_score}, Total={total_score}")
