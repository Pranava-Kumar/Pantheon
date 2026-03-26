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
                logger.debug(f"[{self.model_id}] Generated {signal.direction} signal (conf: {signal.confidence:.2f})")
                return signal
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"[{self.model_id}] Parsing error (attempt {attempt}/3): {e!s:.100}")
                if attempt == 3:
                    return self._failed(str(e), start_time)
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"[{self.model_id}] Fatal extraction error: {e!s:.200}")
                return self._failed(str(e), start_time)
        return self._failed("max retries exceeded", start_time)

    def _parse(self, raw: str) -> ModelSignal:
        import re
        import json
        
        # 1. Clean input: strip thinking tags and markdown fences
        text = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # 2. Heuristic: Look for JSON blocks { ... }
        # Try to find all potential JSON objects
        data = None
        potential_blocks = []
        
        # Simple scan for balanced braces to find candidates
        # This is more robust than regex for nested objects
        stack = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if stack == 0: start_idx = i
                stack += 1
            elif char == '}':
                stack -= 1
                if stack == 0 and start_idx != -1:
                    potential_blocks.append(text[start_idx:i+1])
        
        # 3. Validation: find the one that parses and has our fields
        # Check in reverse (latest is usually the final answer)
        for block in reversed(potential_blocks):
            try:
                candidate = json.loads(block)
                if isinstance(candidate, dict) and "direction" in candidate:
                    data = candidate
                    break
            except json.JSONDecodeError:
                continue
        
        # Fallback to regex if balance-scan found nothing
        if not data:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        if not data:
            raise ValueError(f"No valid JSON signal found in response: {text[:200]}")
        
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

class CascadingExtractor(BaseExtractor):
    """
    An extractor that supports an internal chain of fallback models.
    """
    def __init__(self):
        self._models = [] # List of (model_name, llm_instance)
        self._preferred_idx = 0
        self._failures = []
        self._max_consecutive_failures = 2

    async def _call_model(self, prompt: str) -> str:
        last_error = None
        
        for idx in range(self._preferred_idx, len(self._models)):
            # If a model has failed too many consecutive times, permanently skip it 
            # (unless it's the absolute last resort fallback)
            if self._failures[idx] >= self._max_consecutive_failures and idx != len(self._models) - 1:
                if self._preferred_idx == idx:
                    logger.info(f"[{self.model_id}] Automatically rerouting permanently past {self._models[idx][0]}")
                    self._preferred_idx += 1
                continue

            model_name, llm = self._models[idx]
            
            try:
                # Verbose requirement: Log attempt
                logger.info(f"[{self.model_id}] Attempting extraction with {model_name}...")
                response = await llm.ainvoke(prompt)
                
                content = ""
                if response and response.content:
                    if isinstance(response.content, str):
                        content = response.content
                    elif isinstance(response.content, list):
                        # Handle multimodal or tool call list response
                        for item in response.content:
                            if isinstance(item, dict) and "text" in item:
                                content += item["text"]
                            elif isinstance(item, str):
                                content += item
                    
                if content:
                    logger.debug(f"[{self.model_id}] Success with {model_name}")
                    self._failures[idx] = 0 
                    return content
                raise ValueError(f"{model_name} returned empty response")
            except Exception as e:
                last_error = e
                err_msg = str(e)
                
                # If rate limited, wait a bit before trying the next fallback
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    wait_time = 2 * (self._failures[idx] + 1)
                    logger.warning(f"[{self.model_id}] {model_name} rate limited. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                
                self._failures[idx] += 1
                logger.warning(
                    f"[{self.model_id}] {model_name} failed ({self._failures[idx]}/{self._max_consecutive_failures}): {e!s:.120}"
                )

        raise RuntimeError(
            f"All {len(self._models)} fallback models exhausted. Last error: {last_error}"
        )
