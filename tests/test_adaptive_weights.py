"""
Tests for adaptive weight manager.
"""

import pytest
from pantheon.mmci.weights import AdaptiveWeightManager, WeightManager


class TestAdaptiveWeightManager:
    """Test adaptive weight management functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh adaptive weight manager for each test."""
        return AdaptiveWeightManager(
            weights={"model_a": 0.5, "model_b": 0.5},
            window_size=10,
            adjustment_threshold=0.1
        )
    
    def test_initial_state(self, manager):
        """Test manager initializes correctly."""
        weights = manager.get_weights()
        assert "model_a" in weights
        assert "model_b" in weights
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_record_outcome(self, manager):
        """Test outcome recording."""
        manager.record_outcome("model_a", "BUY", "BUY")
        manager.record_outcome("model_a", "SELL", "BUY")
        
        assert len(manager.performance_history["model_a"]) == 2
    
    def test_get_model_accuracy(self, manager):
        """Test accuracy calculation."""
        # 3 correct, 1 incorrect = 75% accuracy
        manager.record_outcome("model_a", "BUY", "BUY")
        manager.record_outcome("model_a", "BUY", "BUY")
        manager.record_outcome("model_a", "SELL", "BUY")  # Wrong
        manager.record_outcome("model_a", "BUY", "BUY")
        
        accuracy = manager.get_model_accuracy("model_a")
        assert 0.74 <= accuracy <= 0.76
    
    def test_adjust_weights_outperforming(self, manager):
        """Test weight increase for outperforming model."""
        # Record 80% accuracy (outperforming)
        for i in range(10):
            predicted = "BUY" if i < 8 else "SELL"
            manager.record_outcome("model_a", predicted, "BUY")
        
        # Adjust weights
        new_weights = manager.adjust_weights()
        
        # Model A should have increased weight
        assert new_weights["model_a"] > 0.5
    
    def test_adjust_weights_underperforming(self, manager):
        """Test weight decrease for underperforming model."""
        # Record 20% accuracy (underperforming)
        for i in range(10):
            predicted = "BUY" if i < 2 else "SELL"
            manager.record_outcome("model_a", predicted, "BUY")
        
        # Adjust weights
        new_weights = manager.adjust_weights()
        
        # Model A should have decreased weight
        assert new_weights["model_a"] < 0.5
    
    def test_no_adjustment_insufficient_data(self, manager):
        """Test that weights don't adjust with insufficient data."""
        # Only 3 data points (need 5 minimum)
        manager.record_outcome("model_a", "BUY", "BUY")
        manager.record_outcome("model_a", "BUY", "BUY")
        manager.record_outcome("model_a", "SELL", "BUY")
        
        original_weights = manager.get_weights()
        new_weights = manager.adjust_weights()
        
        # Weights should be unchanged
        assert new_weights == original_weights
    
    def test_window_size_limit(self, manager):
        """Test that history is limited to window size."""
        # Record 15 outcomes (window is 10)
        for i in range(15):
            manager.record_outcome("model_a", "BUY", "BUY")
        
        assert len(manager.performance_history["model_a"]) == 10
    
    def test_get_performance_summary(self, manager):
        """Test performance summary generation."""
        # Record some outcomes
        for i in range(10):
            manager.record_outcome("model_a", "BUY", "BUY")
        
        summary = manager.get_performance_summary()
        
        assert "model_a" in summary
        assert "accuracy" in summary["model_a"]
        assert "trades" in summary["model_a"]
        assert "trend" in summary["model_a"]
        assert summary["model_a"]["trades"] == 10
    
    def test_weights_sum_to_one_after_adjustment(self, manager):
        """Test that weights still sum to 1 after adjustment."""
        # Record mixed outcomes
        for i in range(10):
            predicted = "BUY" if i % 2 == 0 else "SELL"
            manager.record_outcome("model_a", predicted, "BUY")
        
        new_weights = manager.adjust_weights()
        
        # Weights should still sum to 1
        assert abs(sum(new_weights.values()) - 1.0) < 0.01
    
    def test_accuracy_caching(self, manager):
        """Test that accuracy is cached."""
        manager.record_outcome("model_a", "BUY", "BUY")
        
        # First call calculates
        accuracy1 = manager.get_model_accuracy("model_a")
        assert "model_a" in manager.accuracy_cache
        
        # Second call uses cache
        accuracy2 = manager.get_model_accuracy("model_a")
        assert accuracy1 == accuracy2
        
        # Recording new outcome invalidates cache
        manager.record_outcome("model_a", "BUY", "BUY")
        assert "model_a" not in manager.accuracy_cache


class TestWeightManagerCompatibility:
    """Test that AdaptiveWeightManager is compatible with WeightManager."""
    
    def test_inherits_from_weight_manager(self):
        """Test proper inheritance."""
        manager = AdaptiveWeightManager()
        assert isinstance(manager, WeightManager)
    
    def test_base_update_method_works(self):
        """Test that base update method still works."""
        manager = AdaptiveWeightManager()
        
        model_signals = [
            {"model_id": "gemini_pro", "direction": "BUY", "failed": False},
            {"model_id": "gemini_flash", "direction": "BUY", "failed": False},
        ]
        
        new_weights = manager.update(model_signals, "BUY")
        
        assert "gemini_pro" in new_weights
        assert "gemini_flash" in new_weights


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
