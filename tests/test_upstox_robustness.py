import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pantheon.data.upstox_client import UpstoxClient

@pytest.fixture
def mock_upstox():
    with patch("pantheon.data.upstox_client.upstox_client.Configuration"), \
         patch("pantheon.data.upstox_client.upstox_client.ApiClient"), \
         patch("pantheon.data.upstox_client.upstox_client.HistoryV3Api"), \
         patch("pantheon.data.upstox_client.upstox_client.MarketQuoteApi"), \
         patch("pantheon.data.upstox_client.UpstoxClient._load_instruments"):
        client = UpstoxClient(access_token="fake_token")
        client._instrument_map = {"RELIANCE": "NSE_EQ|INE002A01018"}
        return client

def test_validate_symbol_nse(mock_upstox):
    # Should return True for symbols in the map
    assert mock_upstox.validate_symbol("RELIANCE") is True

@patch("pantheon.data.upstox_client.yf.Ticker")
def test_validate_symbol_global(mock_yf, mock_upstox):
    # Should return True if yfinance finds it
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame({"close": [100]})
    mock_yf.return_value = mock_ticker
    
    assert mock_upstox.validate_symbol("AAPL") is True

@patch("pantheon.data.upstox_client.yf.Ticker")
def test_validate_symbol_invalid(mock_yf, mock_upstox):
    # Should return False if not in map and yfinance fails
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    mock_yf.return_value = mock_ticker
    
    assert mock_upstox.validate_symbol("INVALID_TICKER") is False

@patch("pantheon.data.upstox_client.yf.Ticker")
def test_yfinance_fallback_cascading(mock_yf, mock_upstox):
    # Should try symbol.NS then symbol
    mock_ticker_ns = MagicMock()
    mock_ticker_ns.history.return_value = pd.DataFrame() # Fails for .NS
    
    mock_ticker_raw = MagicMock()
    mock_ticker_raw.history.return_value = pd.DataFrame({"close": [150], "open": [100], "high": [160], "low": [90], "volume": [1000]})
    mock_ticker_raw.reset_index.return_value = pd.DataFrame({"Date": ["2026-03-26"], "Close": [150], "Open": [100], "High": [160], "Low": [90], "Volume": [1000]})

    def side_effect(ticker_name):
        if ticker_name == "AAPL.NS":
            return mock_ticker_ns
        return mock_ticker_raw

    mock_yf.side_effect = side_effect
    
    df = mock_upstox._yfinance_fallback("AAPL", days=1)
    assert not df.empty
    assert mock_yf.call_count >= 2
