import pandas as pd
import pytest
from pantheon.data.indicators import compute_indicators

def test_rsi_calculation_basic():
    # Simple uptrend for RSI > 50
    data = {
        "close": [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128],
        "high": [101]*15,
        "low": [99]*15,
        "volume": [1000]*15
    }
    df = pd.DataFrame(data)
    result = compute_indicators(df)
    
    assert result["rsi_14"] is not None
    assert result["rsi_14"] > 50

def test_rsi_calculation_downtrend():
    # Simple downtrend for RSI < 50
    data = {
        "close": [128, 126, 124, 122, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100],
        "high": [129]*15,
        "low": [99]*15,
        "volume": [1000]*15
    }
    df = pd.DataFrame(data)
    result = compute_indicators(df)
    
    assert result["rsi_14"] is not None
    assert result["rsi_14"] < 50

def test_compute_indicators_empty_df():
    df = pd.DataFrame()
    result = compute_indicators(df)
    assert all(v is None for v in result.values())

def test_macd_calculation():
    # Price oscillating for MACD signals
    data = {
        "close": [100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 
                  101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101,
                  102, 103, 104, 105, 106],
        "high": [107]*35,
        "low": [99]*35,
        "volume": [1000]*35
    }
    df = pd.DataFrame(data)
    result = compute_indicators(df)
    
    assert result["macd_line"] is not None
    assert result["macd_signal"] is not None
    assert result["macd_hist"] is not None

def test_moving_averages():
    # Data with 200 rows for MA200
    data = {
        "close": [100 + i for i in range(250)],
        "high": [101 + i for i in range(250)],
        "low": [99 + i for i in range(250)],
        "volume": [1000]*250
    }
    df = pd.DataFrame(data)
    result = compute_indicators(df)
    
    assert result["ema_20"] is not None
    assert result["ema_50"] is not None
    assert result["ema_200"] is not None
    assert result["ema_20"] > result["ema_50"] > result["ema_200"]
