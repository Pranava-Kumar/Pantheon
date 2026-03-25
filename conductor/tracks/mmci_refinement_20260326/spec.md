# Track Specification: Implement and Refine MMCI Indicator Calculation

## Goal
The goal of this track is to refine and implement robust calculation logic for the Market Mood Context Index (MMCI) indicators. This includes ensuring accurate technical analysis, integrating news-based sentiment scores, and establishing a clear weighting system for final stock scoring.

## Scope
- **Technical Indicators:** Implement and verify calculations for key technical indicators (RSI, MACD, Moving Averages) using `pandas-ta-classic`.
- **Sentiment Integration:** Connect the LLM-based news extraction outputs (Gemini/Groq) to the MMCI scoring framework.
- **Weighting System:** Refine the `weights.py` and `scoring.py` logic to correctly apply configurable weights to different indicator categories.
- **Data Integrity:** Ensure that indicator calculations handle missing data and outliers gracefully.

## Technical Details
- **Language:** Python
- **Libraries:** `pandas`, `pandas-ta-classic`, `sqlmodel`, `langgraph`
- **Data Sources:** `nse_client.py`, `news_client.py`
- **Components:** `pantheon/mmci/scoring.py`, `pantheon/mmci/weights.py`, `pantheon/data/indicators.py`

## Acceptance Criteria
- [ ] Technical indicators are calculated accurately and verified against known benchmarks.
- [ ] News sentiment scores are successfully integrated into the MMCI total score.
- [ ] The weighting system correctly prioritizes indicators as per `weights.yaml` configuration.
- [ ] Unit tests cover at least 80% of the refinement logic.
