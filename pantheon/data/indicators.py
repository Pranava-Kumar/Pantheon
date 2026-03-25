import pandas as pd
import pandas_ta_classic as ta
import sys
import io
from loguru import logger

def compute_indicators(df: pd.DataFrame) -> dict:
    """
    Computes technical indicators for a given DataFrame of price data.
    All values are taken from the last row (most recent data).
    """
    result = {
        "rsi_14": None,
        "macd_line": None,
        "macd_signal": None,
        "macd_hist": None,
        "bb_upper": None,
        "bb_lower": None,
        "ema_20": None,
        "ema_50": None,
        "ema_200": None,
        "atr_14": None,
        "volume_ratio": None,
    }

    try:
        if df is None or df.empty:
            return result

        def get_last(series):
            if series is None or series.empty:
                return None
            val = series.iloc[-1]
            return float(val) if pd.notna(val) else None

        # Capture pandas_ta's stdout if it gets noisy, but keep track of real failures
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            try:
                result["rsi_14"] = get_last(ta.rsi(df["close"], length=14))
            except Exception as e:
                logger.debug(f"RSI calculation failed: {e}")

            try:
                macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
                if macd is not None and not macd.empty:
                    result["macd_line"] = get_last(macd.get("MACD_12_26_9"))
                    result["macd_hist"] = get_last(macd.get("MACDh_12_26_9"))
                    result["macd_signal"] = get_last(macd.get("MACDs_12_26_9"))
            except Exception as e:
                logger.debug(f"MACD calculation failed: {e}")

            try:
                bb = ta.bbands(df["close"], length=20)
                if bb is not None and not bb.empty:
                    result["bb_lower"] = get_last(bb.get("BBL_20_2.0"))
                    result["bb_upper"] = get_last(bb.get("BBU_20_2.0"))
            except Exception as e:
                logger.debug(f"Bollinger Bands calculation failed: {e}")

            try:
                result["ema_20"] = get_last(ta.ema(df["close"], length=20))
            except Exception as e:
                logger.debug(f"EMA 20 failed: {e}")

            try:
                result["ema_50"] = get_last(ta.ema(df["close"], length=50))
            except Exception as e:
                logger.debug(f"EMA 50 failed: {e}")

            try:
                result["ema_200"] = get_last(ta.ema(df["close"], length=200))
            except Exception as e:
                logger.debug(f"EMA 200 failed: {e}")

            try:
                result["atr_14"] = get_last(ta.atr(df["high"], df["low"], df["close"], length=14))
            except Exception as e:
                logger.debug(f"ATR 14 failed: {e}")

            try:
                vol_sma20 = get_last(ta.sma(df["volume"], length=20))
                today_vol = get_last(df["volume"])
                if vol_sma20 is not None and today_vol is not None and vol_sma20 > 0:
                    result["volume_ratio"] = today_vol / vol_sma20
            except Exception as e:
                logger.debug(f"Volume Ratio failed: {e}")
        finally:
            sys.stdout = old_stdout

    except Exception as e:
        logger.error(f"compute_indicators fatal error: {e}")

    return result

