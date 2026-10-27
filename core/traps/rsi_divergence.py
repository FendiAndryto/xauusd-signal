from typing import List, Dict, Optional
import pandas as pd
from ta.momentum import RSIIndicator

from . import TrapResult
from .sweep import find_swings

def detect_rsi_divergence(
    candles: List[Dict],
    rsi_period: int = 14,
    ob_threshold: float = 65.0,
    os_threshold: float = 35.0
) -> Optional[TrapResult]:
    """
    Detect Secondary Sweep with RSI Divergence.
    Retail counter-trenders get wrecked on the first divergence; the secondary sweep traps both breakout & early counter-trenders.
    """
    n = len(candles)
    if n < rsi_period + 8:
        return None

    # Calculate RSI
    closes = pd.Series([c["close"] for c in candles])
    rsi_series = RSIIndicator(close=closes, window=rsi_period).rsi()
    if rsi_series.isna().iloc[-1]:
        return None

    last = candles[-1]
    last_rsi = float(rsi_series.iloc[-1])

    swing_highs, swing_lows = find_swings(candles[:-1], lookback=3)

    # 1. Bearish Divergence Secondary Sweep -> SELL
    if swing_highs:
        # Check against recent swing highs within last 30 bars
        for sh in reversed(swing_highs):
            if n - 1 - sh["index"] > 30:
                break
            prev_rsi = float(rsi_series.iloc[sh["index"]])

            # Higher high in price, but lower high in RSI + extreme condition
            if last["high"] > sh["price"] and last_rsi < prev_rsi:
                if prev_rsi >= ob_threshold or last_rsi >= ob_threshold:
                    # Rejection candle
                    if last["close"] < last["open"] or last["close"] < sh["price"]:
                        return TrapResult(
                            trap_type="RSI_DIV_SWEEP",
                            direction="SELL",
                            key_level=sh["price"],
                            sweep_extreme=last["high"],
                            time=last["time"],
                            confidence=0.86,
                            detail=f"RSI Divergence Secondary Sweep: Harga cetak higher high ke {last['high']:.2f} tapi RSI melemah ({prev_rsi:.1f} -> {last_rsi:.1f})."
                        )

    # 2. Bullish Divergence Secondary Sweep -> BUY
    if swing_lows:
        for sl in reversed(swing_lows):
            if n - 1 - sl["index"] > 30:
                break
            prev_rsi = float(rsi_series.iloc[sl["index"]])

            # Lower low in price, but higher low in RSI + extreme condition
            if last["low"] < sl["price"] and last_rsi > prev_rsi:
                if prev_rsi <= os_threshold or last_rsi <= os_threshold:
                    # Rejection candle
                    if last["close"] > last["open"] or last["close"] > sl["price"]:
                        return TrapResult(
                            trap_type="RSI_DIV_SWEEP",
                            direction="BUY",
                            key_level=sl["price"],
                            sweep_extreme=last["low"],
                            time=last["time"],
                            confidence=0.86,
                            detail=f"RSI Divergence Secondary Sweep: Harga cetak lower low ke {last['low']:.2f} tapi RSI menguat ({prev_rsi:.1f} -> {last_rsi:.1f})."
                        )

    return None
