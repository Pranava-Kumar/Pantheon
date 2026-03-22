import json
import asyncio
import time
from abc import ABC, abstractmethod
from loguru import logger
from pydantic import BaseModel
from dataclasses import dataclass, asdict

@dataclass
class ModelSignal:
    model_id: str
    direction: str          # "BUY", "HOLD", or "SELL"
    confidence: float       # 0.0 to 1.0
    timeframe: str          # "SHORT", "MEDIUM", or "LONG"
    reasoning: str          # max 500 chars
    price_target: float | None = None
    failed: bool = False
    failure_reason: str = ""
    latency_ms: int = 0

    def signed_confidence(self) -> float:
        if self.direction == "BUY":
            direction_int = 1
        elif self.direction == "SELL":
            direction_int = -1
        else:
            direction_int = 0
            
        return direction_int * self.confidence

    def to_dict(self) -> dict:
        return asdict(self)

class BaseExtractor(ABC):
    model_id: str

    @abstractmethod
    async def _call_model(self, prompt: str) -> str:
        pass

    async def extract(self, prompt: str) -> ModelSignal:
        start_time = time.monotonic()
        for attempt in range(1, 4):
            try:
                raw = await self._call_model(prompt)
                signal = self._parse(raw)
                signal.latency_ms = int((time.monotonic() - start_time) * 1000)
                return signal
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == 3:
                    return self._failed(str(e), start_time)
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                return self._failed(str(e), start_time)
        return self._failed("max retries exceeded", start_time)

    def _parse(self, raw: str) -> ModelSignal:
        # Strip markdown fences
        text = raw.strip()
        if text.startswith("```"):
            try:
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            except IndexError:
                pass
        
        # Extract first JSON object found (handles preamble text)
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response: {text[:200]}")
        text = match.group(0)
        
        data = json.loads(text)
        data["model_id"] = self.model_id
        # Normalize direction
        direction = str(data.get("direction", "HOLD")).upper()
        if direction not in ("BUY", "HOLD", "SELL"):
            direction = "HOLD"
        data["direction"] = direction
        # Clamp confidence
        data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.0))))
        # Validate timeframe
        timeframe = str(data.get("timeframe", "MEDIUM")).upper()
        if timeframe not in ("SHORT", "MEDIUM", "LONG"):
            timeframe = "MEDIUM"
        data["timeframe"] = timeframe
        # Truncate reasoning
        data["reasoning"] = str(data.get("reasoning", ""))[:500]
        data.setdefault("price_target", None)
        data.setdefault("failed", False)
        data.setdefault("failure_reason", "")
        data.setdefault("latency_ms", 0)
        return ModelSignal(**{k: v for k, v in data.items() 
                             if k in ModelSignal.__dataclass_fields__})

    def _failed(self, reason: str, start_time: float) -> ModelSignal:
        return ModelSignal(
            model_id=self.model_id,
            direction="HOLD",
            confidence=0.0,
            timeframe="MEDIUM",
            reasoning="",
            failed=True,
            failure_reason=reason[:200],
            latency_ms=int((time.monotonic() - start_time) * 1000)
        )
