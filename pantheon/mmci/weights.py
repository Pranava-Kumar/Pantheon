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
    def __init__(self, weights: dict = None):
        self._w = dict(weights or INITIAL_WEIGHTS)

    def get_weights(self) -> dict:
        return dict(self._w)

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
        n = len(self._w)
        if any(v < WEIGHT_FLOOR or v > WEIGHT_CEILING for v in self._w.values()):
            uniform = 1.0 / n
            self._w = {k: 0.7*v + 0.3*uniform for k, v in self._w.items()}
