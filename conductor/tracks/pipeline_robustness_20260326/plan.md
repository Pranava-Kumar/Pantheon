# Implementation Plan: Pipeline Reliability and Global Symbol Support

## Phase 1: Smarter Symbol Validation and Auto-Detection [checkpoint: ad5f196]

### 1.1: UpstoxClient Refactor
- [x] Task: Update `UpstoxClient` with symbol validation and global fallback
    - [x] Write unit tests for `validate_symbol` and `_yfinance_fallback` with NSE and US tickers
    - [x] Implement `validate_symbol` method in `UpstoxClient`
    - [x] Update `_yfinance_fallback` to attempt raw symbol retrieval if `.NS` suffix fails

### 1.2: Runner Enhancement
- [x] Task: Enhance `run_analysis.py` with early validation [aabc49f]
    - [x] Implement early symbol check before building context [aabc49f]
    - [x] Add graceful skip logic with clear ANSI-colored error messages for invalid symbols [aabc49f]

- [x] Task: Conductor - User Manual Verification 'Phase 1: Smarter Symbol Validation and Auto-Detection' (Protocol in workflow.md) [ad5f196]

## Phase 2: Cascading Groq Extractors and Better Logging

### 2.1: Base Extractor Evolution
- [x] Task: Update `BaseExtractor` or create `CascadingExtractor` [707a7b4]
    - [x] Write unit tests for internal fallback chains and retry logic [707a7b4]
    - [x] Implement robust cascading fallback logic (similar to GeminiPro) in a reusable way [707a7b4]

### 2.2: Groq Refactor
- [x] Task: Refactor Groq Extractors to use cascading fallbacks [707a7b4]
    - [x] Update `GroqLlamaExtractor`, `GroqQwenExtractor`, and `GroqGPTExtractor` with tiered model lists [707a7b4]
    - [x] Ensure all fallback attempts and node starts are logged at the appropriate verbosity level [707a7b4]

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Cascading Groq Extractors and Better Logging' (Protocol in workflow.md)

## Phase 3: Integration and Robustness Testing

### 3.1: End-to-End Pipeline Validation
- [ ] Task: Verify full pipeline with global symbols and model failures
    - [ ] Write integration tests simulating 429 errors and invalid symbols
    - [ ] Ensure the final CLI output reflects the "Verbose Retries" and "Auto-Detect" requirements

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration and Robustness Testing' (Protocol in workflow.md)
