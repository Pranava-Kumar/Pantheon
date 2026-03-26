# Track Specification: Pipeline Reliability and Global Symbol Support

## Goal
Improve the reliability of the analysis pipeline by ensuring all configured models (including Groq) are utilized with robust fallbacks, and expand stock support to global markets with graceful validation.

## Scope
- **Symbol Validation (Auto-Detect):** Update `UpstoxClient` and `ContextBuilder` to validate symbols. If an NSE symbol is not found, automatically attempt to resolve it as a global/US symbol via `yfinance`.
- **Early Termination:** Implement logic in `run_analysis.py` to stop analysis immediately if a symbol cannot be resolved, providing a clear "Invalid Symbol" error.
- **Groq Cascading Fallbacks:** Implement a fallback chain for Groq extractors (similar to `GeminiProExtractor`) to handle rate limits and service outages.
- **Verbose Pipeline Reporting:** Update `LangGraph` nodes and `BaseExtractor` to log detailed attempt/fallback information to the console during execution.

## Functional Requirements
1. **UpstoxClient Refactor:**
   - Add `validate_symbol(symbol: str) -> bool`.
   - Update `get_historical_ohlcv` to try the raw symbol if the `.NS` suffix fails on `yfinance`.
2. **Cascading Groq Extractors:**
   - Create a base `CascadingExtractor` class or update `BaseExtractor` to support internal fallback chains.
   - Update `GroqLlamaExtractor` to fallback to `mixtral-8x7b-32768` and `qwen-2.5-32b` on Groq.
3. **Pipeline Verbosity:**
   - Log the start of each model node execution.
   - Log each fallback attempt within an extractor at `WARNING` level.
4. **ContextBuilder Hard-Stop:**
   - `build()` method should raise a `SymbolNotFoundError` if no price data can be found, allowing the runner to skip the symbol.

## Acceptance Criteria
- [ ] Running `run_analysis.py --symbols AAPL` resolves to US market data and completes successfully.
- [ ] Running a non-existent symbol (e.g., `XYZABC`) stops immediately with a "Symbol Not Found" error.
- [ ] Groq model failures (429/500) trigger automatic fallbacks to other Groq models.
- [ ] The CLI output shows real-time progress of each model and its retry status.
