from typing import Annotated, TypedDict
import operator

class PantheonState(TypedDict, total=False):
    symbol: str
    run_id: str
    stock_context: dict
    market_regime: str
    model_prompts: dict
    model_signals: Annotated[list, operator.add]
    dissent_score: float
    dissent_flag: bool
    consensus_score: float
    final_direction: str
    suggested_alloc: float
    risk_level: int
    price_target: float | None
    final_signal: dict
    started_at: str
    errors: list
