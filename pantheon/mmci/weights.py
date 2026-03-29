import yaml
from pathlib import Path

# Path to the weights configuration file
WEIGHTS_FILE = Path(__file__).resolve().parent.parent / "config" / "weights.yaml"

INITIAL_CATEGORY_WEIGHTS = {
    "technicals": 0.40,
    "fundamentals": 0.30,
    "sentiment": 0.30
}

INITIAL_WEIGHTS = {
    "gemini_pro": 0.25,
    "gemini_flash": 0.20,
    "groq_qwen": 0.20,
    "groq_llama": 0.20,
    "groq_gpt": 0.15
}

LEARNING_RATE = 0.05
WEIGHT_FLOOR = 0.05
WEIGHT_CEILING = 0.40


def load_config_weights():
    try:
        with open(WEIGHTS_FILE, "r") as f:
            config = yaml.safe_load(f)
            return config.get("models", INITIAL_WEIGHTS), config.get("categories", INITIAL_CATEGORY_WEIGHTS)
    except Exception:
        return INITIAL_WEIGHTS, INITIAL_CATEGORY_WEIGHTS


class WeightManager:
    """
    Manages model weights for the MMCI scoring system.
    
    Handles weight initialization, normalization, bounds enforcement,
    and performance-based updates via reinforcement learning.
    """
    
    def __init__(self, weights: dict = None, category_weights: dict = None):
        w_cfg, cw_cfg = load_config_weights()
        self._w = dict(weights) if weights is not None else dict(w_cfg)
        self._cw = dict(category_weights) if category_weights is not None else dict(cw_cfg)
    
    def get_weights(self) -> dict:
        return dict(self._w)
    
    def get_category_weights(self) -> dict:
        return dict(self._cw)
    
    def update(self, model_signals: list[dict], actual_direction: str) -> dict:
        for s in model_signals:
            if s.get("failed"):
                continue
            mid = s["model_id"]
            if mid not in self._w:
                continue
            correct = 1.0 if s["direction"] == actual_direction else 0.0
            self._w[mid] = self._w[mid] + LEARNING_RATE * (correct - self._w[mid])
        self._normalize()
        self._apply_bounds()
        self._normalize()
        return self.get_weights()
    
    def _normalize(self):
        total = sum(self._w.values())
        if total > 0:
            self._w = {k: v/total for k, v in self._w.items()}
    
    def _apply_bounds(self):
        """Enforces floor and ceiling bounds while maintaining sum-to-1."""
        n = len(self._w)
        if n == 0:
            return
        
        effective_floor = min(WEIGHT_FLOOR, 1.0/n)
        effective_ceiling = max(WEIGHT_CEILING, 1.0/n)
        
        for _ in range(10):
            total = sum(self._w.values())
            if abs(total - 1.0) < 1e-6:
                if all(effective_floor - 1e-9 <= v <= effective_ceiling + 1e-9 for v in self._w.values()):
                    break
            
            new_w = {}
            for k, v in self._w.items():
                new_w[k] = max(effective_floor, min(effective_ceiling, v))
            
            new_total = sum(new_w.values())
            if new_total > 0:
                self._w = {k: v/new_total for k, v in new_w.items()}
            else:
                self._w = {k: 1.0/n for k in new_w}


class AdaptiveWeightManager(WeightManager):
    """
    Extends WeightManager with dynamic weight adjustment based on model performance.
    
    Features:
    - Tracks model accuracy over rolling window (last 20 trades)
    - Automatically reduces weight of underperforming models (<40% accuracy)
    - Automatically increases weight of outperforming models (>60% accuracy)
    - Maintains weight bounds and sum-to-1 constraint
    """
    
    def __init__(self, weights: dict = None, category_weights: dict = None,
                 window_size: int = 20, adjustment_threshold: float = 0.1):
        super().__init__(weights, category_weights)
        
        self.window_size = window_size
        self.adjustment_threshold = adjustment_threshold
        self.performance_history = {mid: [] for mid in self._w.keys()}
        self.accuracy_cache = {}
    
    def record_outcome(self, model_id: str, predicted: str, actual: str):
        """Record model prediction outcome for performance tracking."""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []
        
        self.performance_history[model_id].append({
            'predicted': predicted,
            'actual': actual,
            'correct': predicted == actual,
        })
        
        if len(self.performance_history[model_id]) > self.window_size:
            self.performance_history[model_id].pop(0)
        
        self.accuracy_cache = {}
    
    def get_model_accuracy(self, model_id: str) -> float:
        """Get model's recent accuracy percentage."""
        if model_id in self.accuracy_cache:
            return self.accuracy_cache[model_id]
        
        history = self.performance_history.get(model_id, [])
        if not history:
            return 0.5
        
        correct = sum(1 for h in history if h['correct'])
        accuracy = correct / len(history)
        self.accuracy_cache[model_id] = accuracy
        return accuracy
    
    def adjust_weights(self):
        """Adjust model weights based on recent performance."""
        adjustments = {}
        
        for model_id in self._w.keys():
            accuracy = self.get_model_accuracy(model_id)
            
            if len(self.performance_history.get(model_id, [])) < 5:
                continue
            
            if accuracy > 0.6:
                factor = 1.0 + (accuracy - 0.5) * self.adjustment_threshold
                adjustments[model_id] = self._w[model_id] * factor
            elif accuracy < 0.4:
                factor = 1.0 - (0.5 - accuracy) * self.adjustment_threshold
                adjustments[model_id] = self._w[model_id] * factor
        
        if adjustments:
            self._w.update(adjustments)
            self._normalize()
            self._apply_bounds()
            self._normalize()
        
        return self.get_weights()
    
    def get_performance_summary(self) -> dict:
        """Get summary of all model performances."""
        summary = {}
        
        for model_id, history in self.performance_history.items():
            if not history:
                continue
            
            accuracy = self.get_model_accuracy(model_id)
            
            if len(history) >= 10:
                recent_accuracy = sum(1 for h in history[-5:] if h['correct']) / 5
                previous_accuracy = sum(1 for h in history[-10:-5] if h['correct']) / 5
                
                if recent_accuracy > previous_accuracy + 0.1:
                    trend = "improving"
                elif recent_accuracy < previous_accuracy - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            summary[model_id] = {
                'accuracy': round(accuracy, 3),
                'trades': len(history),
                'trend': trend,
            }
        
        return summary
