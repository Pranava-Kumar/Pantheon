"""
Market regime detection module.

Provides functions to detect market regime (BULL, BEAR, SIDEWAYS) based on
Nifty 50 price action relative to its 200-day moving average.
"""

from loguru import logger
from pantheon.data.upstox_client import UpstoxClient
from pantheon.config.settings import settings


async def detect_market_regime(upstox: UpstoxClient) -> str:
    """
    Detect the current market regime based on Nifty 50 price vs 200-day MA.

    Args:
        upstox: Configured UpstoxClient instance.

    Returns:
        str: Market regime - "BULL", "BEAR", or "SIDEWAYS".
    """
    try:
        df = upstox.get_nifty50_history(days=250)
        ma200 = df["close"].tail(200).mean()
        last = df["close"].iloc[-1]

        if last > ma200 * settings.BULL_MA200_MULTIPLIER:
            return "BULL"
        if last < ma200 * settings.BEAR_MA200_MULTIPLIER:
            return "BEAR"

        return "SIDEWAYS"
    except Exception as e:
        logger.warning(f"Regime detection failed: {e}, defaulting to SIDEWAYS")
        return "SIDEWAYS"


def calculate_regime_from_dataframe(df) -> str:
    """
    Calculate market regime from a DataFrame with OHLCV data.

    Utility function for use when UpstoxClient is not available.

    Args:
        df: DataFrame with 'close' column containing price data.

    Returns:
        str: Market regime - "BULL", "BEAR", or "SIDEWAYS".
    """
    try:
        if df is None or df.empty:
            return "SIDEWAYS"

        ma200 = df["close"].tail(200).mean()
        last = df["close"].iloc[-1]

        if last > ma200 * settings.BULL_MA200_MULTIPLIER:
            return "BULL"
        if last < ma200 * settings.BEAR_MA200_MULTIPLIER:
            return "BEAR"

        return "SIDEWAYS"
    except Exception as e:
        logger.warning(f"Regime calculation failed: {e}, defaulting to SIDEWAYS")
        return "SIDEWAYS"
