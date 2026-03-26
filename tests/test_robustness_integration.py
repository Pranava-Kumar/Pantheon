import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
from pantheon.extractors.base import CascadingExtractor, ModelSignal
from pantheon.data.upstox_client import UpstoxClient

class MockLLM:
    def __init__(self, response=None, error_code=None):
        self.response = response
        self.error_code = error_code
        self.call_count = 0

    async def ainvoke(self, prompt):
        self.call_count += 1
        if self.error_code == 429:
            raise RuntimeError("RESOURCE_EXHAUSTED")
        if self.error_code == 404:
            raise RuntimeError("NOT_FOUND")
        mock_resp = MagicMock()
        mock_resp.content = self.response
        return mock_resp

class DummyCascade(CascadingExtractor):
    model_id = "dummy"
    def __init__(self, models):
        super().__init__()
        self._models = models
        self._failures = [0] * len(models)

@pytest.mark.asyncio
async def test_full_cascade_with_429_recovery():
    # Model 1 fails 429, Model 2 succeeds
    llm1 = MockLLM(error_code=429)
    llm2 = MockLLM(response='{"direction": "BUY", "confidence": 0.8, "reasoning": "test"}')
    
    extractor = DummyCascade([("m1", llm1), ("m2", llm2)])
    
    # We need to monkeypatch sleep to avoid actual waiting in tests
    with patch("asyncio.sleep", return_value=None):
        signal = await extractor.extract("test")
        
    assert signal.direction == "BUY"
    assert llm1.call_count == 1
    assert llm2.call_count == 1

@pytest.mark.asyncio
async def test_full_cascade_exhaustion_reporting():
    # All models fail
    llm1 = MockLLM(error_code=429)
    llm2 = MockLLM(error_code=404)
    
    extractor = DummyCascade([("m1", llm1), ("m2", llm2)])
    
    with patch("asyncio.sleep", return_value=None):
        signal = await extractor.extract("test")
        
    assert signal.failed is True
    assert "exhausted" in signal.failure_reason

def test_upstox_quiet_validation_success():
    with patch("pantheon.data.upstox_client.upstox_client.Configuration"), \
         patch("pantheon.data.upstox_client.upstox_client.ApiClient"), \
         patch("pantheon.data.upstox_client.yf.Ticker") as mock_yf:
        
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame({"close": [100]})
        mock_yf.return_value = mock_ticker
        
        client = UpstoxClient(access_token="fake")
        client._instrument_map = {}
        
        # This should not print anything to stdout/stderr due to redirection
        assert client.validate_symbol("AAPL") is True
