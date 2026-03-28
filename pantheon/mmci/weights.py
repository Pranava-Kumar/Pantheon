import yaml
from pathlib import Path

# Path to the weights configuration file
WEIGHTS_FILE = Path(__file__).resolve().parent.parent / "config" / "weights.yaml"

INITIAL_CATEGORY_WEIGHTS = {
    "technicals": 0.40,
    "fundamentals": 0.30,
    "sentiment": 0.30
}

def load_config_weights():
    try:
        with open(WEIGHTS_FILE, "r") as f:
            config = yaml.safe_load(f)
            return config.get("models", INITIAL_WEIGHTS), config.get("categories", INITIAL_CATEGORY_WEIGHTS)
    except Exception:
        return INITIAL_WEIGHTS, INITIAL_CATEGORY_WEIGHTS

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

class WeightManager:
    """
    Manages model weights for the MMCI scoring system.
    
    Handles weight initialization, normalization, bounds enforcement,
    and performance-based updates via reinforcement learning.
    
    Attributes:
        _w: Dictionary mapping model_id to weight value.
        _cw: Dictionary mapping category to weight value.
    """
    
    def __init__(self, weights: dict = None, category_weights: dict = None):
        # Always get defaults
        w_cfg, cw_cfg = load_config_weights()
        self._w = dict(weights) if weights is not None else dict(w_cfg)
        self._cw = dict(category_weights) if category_weights is not None else dict(cw_cfg)

    def get_weights(self) -> dict:
        return dict(self._w)

    def get_category_weights(self) -> dict:
        return dict(self._cw)

    def update(self, model_signals: list[dict], actual_direction: str) -> dict:
        for s in model_signals:
            if s.get("failed"): continue
            mid = s["model_id"]
            if mid not in self._w: continue
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
        """
        Strictly enforces floor and ceiling bounds while maintaining sum-to-1.
        Uses an iterative approach to redistribute excess weight.
        """
        n = len(self._w)
        if n == 0: return
        
        # Ensure floor * n <= 1.0 and ceiling * n >= 1.0
        # Otherwise, the bounds are mathematically impossible
        effective_floor = min(WEIGHT_FLOOR, 1.0/n)
        effective_ceiling = max(WEIGHT_CEILING, 1.0/n)

        for _ in range(10): # Iterative redistribution
            total = sum(self._w.values())
            if abs(total - 1.0) < 1e-6:
                # Check if all in bounds
                if all(effective_floor - 1e-9 <= v <= effective_ceiling + 1e-9 for v in self._w.values()):
                    break
            
            # Clamp
            new_w = {}
            for k, v in self._w.items():
                new_w[k] = max(effective_floor, min(effective_ceiling, v))
            
            # Normalize
            new_total = sum(new_w.values())
            if new_total > 0:
                self._w = {k: v/new_total for k, v in new_w.items()}
            else:
                self._w = {k: 1.0/n for k in new_w}
