import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from pantheon.extractors.base import CascadingExtractor, ModelSignal

class MockLLM:
    def __init__(self, response=None, should_fail=False):
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0

    async def ainvoke(self, prompt):
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("API Error")
        mock_resp = MagicMock()
        mock_resp.content = self.response
        return mock_resp

class SimpleCascadingExtractor(CascadingExtractor):
    model_id = "test_cascade"
    def __init__(self, models):
        super().__init__()
        self._models = models
        self._failures = [0] * len(models)

@pytest.mark.asyncio
async def test_cascading_success_first_try():
    llm1 = MockLLM(response='{"direction": "BUY", "confidence": 0.9}')
    llm2 = MockLLM(response='{"direction": "SELL", "confidence": 0.5}')
    
    extractor = SimpleCascadingExtractor([("m1", llm1), ("m2", llm2)])
    signal = await extractor.extract("test prompt")
    
    assert signal.direction == "BUY"
    assert llm1.call_count == 1
    assert llm2.call_count == 0

@pytest.mark.asyncio
async def test_cascading_fallback():
    llm1 = MockLLM(should_fail=True)
    llm2 = MockLLM(response='{"direction": "SELL", "confidence": 0.5}')
    
    extractor = SimpleCascadingExtractor([("m1", llm1), ("m2", llm2)])
    signal = await extractor.extract("test prompt")
    
    assert signal.direction == "SELL"
    assert llm1.call_count == 1
    assert llm2.call_count == 1

@pytest.mark.asyncio
async def test_cascading_exhaustion():
    llm1 = MockLLM(should_fail=True)
    llm2 = MockLLM(should_fail=True)
    
    extractor = SimpleCascadingExtractor([("m1", llm1), ("m2", llm2)])
    signal = await extractor.extract("test prompt")
    
    assert signal.failed is True
    assert "exhausted" in signal.failure_reason
    assert llm1.call_count == 1
    assert llm2.call_count == 1
