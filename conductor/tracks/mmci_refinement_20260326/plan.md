# Implementation Plan: Implement and Refine MMCI Indicator Calculation

## Phase 1: Foundation & Technical Indicators

### 1.1: Environment & Baseline Verification
- [x] Task: Verify existing MMCI infrastructure and current indicator outputs
    - [ ] Run current MMCI scoring script and log baseline results
    - [ ] Identify gaps in current technical indicator coverage

### 1.2: Technical Indicator Implementation (TDD)
- [x] Task: Implement robust RSI calculation
    - [x] Write tests for RSI calculation with various market scenarios (overbought, oversold, flat)
    - [x] Refine `pantheon/data/indicators.py` to ensure RSI calculation matches `pandas-ta-classic` standards
- [x] Task: Implement MACD and Moving Average indicators
    - [x] Write tests for MACD signal line and histogram accuracy
    - [x] Implement MACD and SMA/EMA logic in `pantheon/data/indicators.py`

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Technical Indicators' (Protocol in workflow.md)

## Phase 2: Sentiment & Scoring Integration

### 2.1: News Sentiment Mapping
- [ ] Task: Map extractor outputs to MMCI sentiment indicators
    - [ ] Write tests to verify the flow from `gemini_pro.py`/`groq_llama.py` output to MMCI input
    - [ ] Update `pantheon/mmci/scoring.py` to ingest extracted news data and assign sentiment values

### 2.2: Refine Weighting & Final Scoring
- [ ] Task: Update scoring logic to respect `weights.yaml`
    - [ ] Write tests for weighted score calculation across different indicator categories
    - [ ] Refine `pantheon/mmci/scoring.py` to dynamically apply weights from `pantheon/mmci/weights.py`

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Sentiment & Scoring Integration' (Protocol in workflow.md)

## Phase 3: Validation & Quality Assurance

### 3.1: Comprehensive Testing & Coverage
- [ ] Task: Verify total MMCI score calculation
    - [ ] Write integration tests for the full MMCI calculation pipeline (Price -> Indicators -> Sentiment -> Weights -> Final Score)
    - [ ] Ensure unit and integration tests achieve >80% coverage for the `mmci` and `data` modules

### 3.2: Performance & Data Integrity
- [ ] Task: Validate performance and error handling
    - [ ] Test the system with incomplete market/news data to ensure graceful degradation of scores
    - [ ] Perform a final analysis run and verify results against the dashboard (Streamlit)

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Validation & Quality Assurance' (Protocol in workflow.md)
