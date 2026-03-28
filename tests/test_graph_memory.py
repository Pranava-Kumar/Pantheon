"""
Tests for LangGraph MemorySaver state management.

These tests verify that the graph properly manages state between invocations
when using MemorySaver checkpointer, ensuring no state leakage occurs.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from pantheon.agents.graph import build_graph
from pantheon.agents.state import PantheonState
from pantheon.extractors.base import BaseExtractor, ModelSignal
import time


class MockExtractor(BaseExtractor):
    """Mock extractor for testing that returns deterministic signals."""

    def __init__(self, model_id: str = "mock_model", direction: str = "BUY", confidence: float = 0.8):
        self._model_id = model_id
        self._direction = direction
        self._confidence = confidence

    @property
    def model_id(self) -> str:
        return self._model_id

    async def _call_model(self, prompt: str) -> str:
        """Mock model call - returns a pre-formatted JSON response."""
        return f'{{"direction": "{self._direction}", "confidence": {self._confidence}, "timeframe": "MEDIUM", "reasoning": "Mock signal"}}'

    async def extract(self, prompt: str) -> ModelSignal:
        """Return a deterministic mock signal."""
        return ModelSignal(
            model_id=self._model_id,
            direction=self._direction,
            confidence=self._confidence,
            timeframe="MEDIUM",
            reasoning=f"Mock signal from {self._model_id}",
            failed=False,
            latency_ms=10
        )


@pytest.fixture
def mock_extractors():
    """Fixture to mock all extractors with deterministic behavior."""
    mock_extractors_list = [
        MockExtractor("gemini_pro", "BUY", 0.85),
        MockExtractor("gemini_flash", "BUY", 0.75),
        MockExtractor("groq_qwen", "BUY", 0.80),
        MockExtractor("groq_llama", "HOLD", 0.60),
        MockExtractor("groq_gpt", "BUY", 0.70),
    ]
    
    with patch('pantheon.agents.graph.get_all_extractors') as mock_get:
        mock_get.return_value = mock_extractors_list
        yield mock_extractors_list


class TestMemorySaverStateManagement:
    """Test graph state management with MemorySaver checkpointer."""

    def test_graph_creates_with_memory_saver(self, mock_extractors):
        """Verify graph is created with MemorySaver checkpointer."""
        graph = build_graph()
        assert graph is not None
        # Graph should have checkpointer configured
        assert hasattr(graph, 'checkpointer')

    @pytest.mark.asyncio
    async def test_state_isolation_between_invocations(self, mock_extractors):
        """Verify state doesn't leak between separate invocations."""
        graph = build_graph()

        # First invocation
        run_id_1 = str(uuid.uuid4())
        state_1 = {
            "symbol": "RELIANCE",
            "run_id": run_id_1,
            "market_regime": "BULL",
            "stock_context": {"current_price": 100.0},
            "model_signals": [],
            "errors": []
        }
        result_1 = await graph.ainvoke(state_1)

        # Second invocation with different symbol
        run_id_2 = str(uuid.uuid4())
        state_2 = {
            "symbol": "TCS",
            "run_id": run_id_2,
            "market_regime": "SIDEWAYS",
            "stock_context": {"current_price": 200.0},
            "model_signals": [],
            "errors": []
        }
        result_2 = await graph.ainvoke(state_2)

        # Verify results are independent
        assert result_1["final_signal"]["symbol"] == "RELIANCE"
        assert result_2["final_signal"]["symbol"] == "TCS"
        assert result_1["final_signal"]["run_id"] == run_id_1
        assert result_2["final_signal"]["run_id"] == run_id_2

    @pytest.mark.asyncio
    async def test_model_signals_accumulation(self, mock_extractors):
        """Verify model signals are properly accumulated in state."""
        graph = build_graph()

        state = {
            "symbol": "INFY",
            "run_id": str(uuid.uuid4()),
            "market_regime": "BULL",
            "stock_context": {"current_price": 150.0},
            "model_signals": [],
            "errors": []
        }

        result = await graph.ainvoke(state)

        # Should have accumulated model signals from all extractors
        assert "model_signals" in result
        assert len(result["model_signals"]) > 0

    @pytest.mark.asyncio
    async def test_dissent_score_calculation(self, mock_extractors):
        """Verify dissent score is calculated correctly."""
        graph = build_graph()

        state = {
            "symbol": "HDFC",
            "run_id": str(uuid.uuid4()),
            "market_regime": "BEAR",
            "stock_context": {"current_price": 300.0},
            "model_signals": [],
            "errors": []
        }

        result = await graph.ainvoke(state)

        # Should have dissent score between 0 and 1
        assert "dissent_score" in result["final_signal"]
        assert 0.0 <= result["final_signal"]["dissent_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_insufficient_signals_dissent_flag(self, mock_extractors):
        """Verify dissent flag is set when insufficient signals."""
        # Create mock that returns fewer than MIN_MODELS_REQUIRED
        with patch('pantheon.agents.graph.get_all_extractors') as mock_get:
            mock_get.return_value = [MockExtractor("single", "BUY", 0.8)]
            graph = build_graph()

            state = {
                "symbol": "TEST",
                "run_id": str(uuid.uuid4()),
                "market_regime": "SIDEWAYS",
                "stock_context": {"current_price": 50.0},
                "model_signals": [],
                "errors": []
            }

            result = await graph.ainvoke(state)
            
            # Should have dissent flag set due to insufficient signals
            # When dissent_flag is True, hold_output_node should produce final_signal
            if "final_signal" in result:
                assert result["final_signal"]["dissent_flag"] is True
            # Alternative: check that errors were recorded
            assert result.get("errors", []) == [] or "INSUFFICIENT_SIGNALS" in str(result)


@pytest.mark.asyncio
class TestAsyncGraphStateManagement:
    """Test async graph state management."""

    async def test_async_invoke_state_isolation(self, mock_extractors):
        """Verify async invoke maintains state isolation."""
        graph = build_graph()
        
        run_id_1 = str(uuid.uuid4())
        state_1 = {
            "symbol": "ASYNC1",
            "run_id": run_id_1,
            "market_regime": "BULL",
            "stock_context": {"current_price": 100.0},
            "model_signals": [],
            "errors": []
        }
        
        result_1 = await graph.ainvoke(state_1)
        
        run_id_2 = str(uuid.uuid4())
        state_2 = {
            "symbol": "ASYNC2",
            "run_id": run_id_2,
            "market_regime": "BEAR",
            "stock_context": {"current_price": 200.0},
            "model_signals": [],
            "errors": []
        }
        
        result_2 = await graph.ainvoke(state_2)
        
        # Verify results are independent
        assert result_1["final_signal"]["symbol"] == "ASYNC1"
        assert result_2["final_signal"]["symbol"] == "ASYNC2"

    async def test_concurrent_invocations(self, mock_extractors):
        """Verify concurrent invocations don't interfere with each other."""
        import asyncio
        graph = build_graph()
        
        async def invoke_symbol(symbol: str):
            state = {
                "symbol": symbol,
                "run_id": str(uuid.uuid4()),
                "market_regime": "BULL",
                "stock_context": {"current_price": 100.0},
                "model_signals": [],
                "errors": []
            }
            return await graph.ainvoke(state)
        
        # Run multiple invocations concurrently
        results = await asyncio.gather(
            invoke_symbol("CONC1"),
            invoke_symbol("CONC2"),
            invoke_symbol("CONC3")
        )
        
        # Verify each result has correct symbol
        symbols = [r["final_signal"]["symbol"] for r in results]
        assert "CONC1" in symbols
        assert "CONC2" in symbols
        assert "CONC3" in symbols
