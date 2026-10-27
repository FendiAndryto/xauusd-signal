from typing import List, Dict, Optional
from . import TrapResult
from .sweep import find_swings

def detect_equal_levels(
    candles: List[Dict],
    tolerance_pips: float = 1.5,
    min_gap: int = 5
) -> Optional[TrapResult]:
    """
    Detect Equal Highs (EQH) / Equal Lows (EQL) Stop Hunt Sweep.
    Retail double tops / double bottoms are prime liquidity pools for market makers.
    """
    if len(candles) < 25:
        return None

    swing_highs, swing_lows = find_swings(candles[:-1], lookback=3)
    last = candles[-1]

    # 1. Check Equal Highs (EQH) -> Potential SELL
    if len(swing_highs) >= 2:
        for i in range(len(swing_highs) - 1, 0, -1):
            h2 = swing_highs[i]
            for j in range(i - 1, -1, -1):
                h1 = swing_highs[j]
                gap = h2["index"] - h1["index"]
                if gap >= min_gap and abs(h2["price"] - h1["price"]) <= tolerance_pips:
                    eqh_level = max(h1["price"], h2["price"])
                    # Last candle sweeps above the highest EQH and closes back below the lower one
                    if last["high"] > eqh_level and last["close"] < min(h1["price"], h2["price"]):
                        return TrapResult(
                            trap_type="EQH_EQL",
                            direction="SELL",
                            key_level=eqh_level,
                            sweep_extreme=last["high"],
                            time=last["time"],
                            confidence=0.92,
                            detail=f"Double Top Liquidity Purged: Equal Highs di {eqh_level:.2f} disapu ke {last['high']:.2f} sebelum banting balik."
                        )

    # 2. Check Equal Lows (EQL) -> Potential BUY
    if len(swing_lows) >= 2:
        for i in range(len(swing_lows) - 1, 0, -1):
            l2 = swing_lows[i]
            for j in range(i - 1, -1, -1):
                l1 = swing_lows[j]
                gap = l2["index"] - l1["index"]
                if gap >= min_gap and abs(l2["price"] - l1["price"]) <= tolerance_pips:
                    eql_level = min(l1["price"], l2["price"])
                    # Last candle sweeps below the lowest EQL and closes back above the higher one
                    if last["low"] < eql_level and last["close"] > max(l1["price"], l2["price"]):
                        return TrapResult(
                            trap_type="EQH_EQL",
                            direction="BUY",
                            key_level=eql_level,
                            sweep_extreme=last["low"],
                            time=last["time"],
                            confidence=0.92,
                            detail=f"Double Bottom Liquidity Purged: Equal Lows di {eql_level:.2f} disapu ke {last['low']:.2f} sebelum mental naik."
                        )

    return None
