from typing import List, Dict, Optional
from . import TrapResult

def detect_ifvg_breaker(candles: List[Dict], max_age: int = 25) -> Optional[TrapResult]:
    """
    Detect SMC Inducement Breaker (Inverse Fair Value Gap).
    When an institutional FVG gets invalidated/breached, it inverts into a support/resistance breaker.
    """
    n = len(candles)
    if n < 8:
        return None

    last = candles[-1]
    lookback_start = max(0, n - max_age)

    # Scan for prior FVGs that were breached
    for i in range(lookback_start + 1, n - 2):
        c1 = candles[i - 1]
        c2 = candles[i]
        c3 = candles[i + 1]

        # 1. Bullish FVG check
        if c3["low"] > c1["high"] + 0.4:
            fvg_top = c3["low"]
            fvg_bottom = c1["high"]

            # Did a subsequent candle breach below fvg_bottom?
            breached = False
            for k in range(i + 2, n - 1):
                if candles[k]["close"] < fvg_bottom:
                    breached = True
                    break

            # If breached, it becomes an IFVG (Resistance).
            # Last candle retests this zone from below and rejects:
            if breached and last["open"] <= fvg_bottom and last["high"] >= fvg_bottom and last["close"] < fvg_bottom:
                return TrapResult(
                    trap_type="IFVG_BREAKER",
                    direction="SELL",
                    key_level=fvg_bottom,
                    sweep_extreme=last["high"],
                    time=last["time"],
                    confidence=0.88,
                    detail=f"SMC Inducement Breached: Bullish FVG di {fvg_bottom:.2f} jebol dan di-retest sebagai Inverse FVG Resistance."
                )

        # 2. Bearish FVG check
        elif c3["high"] < c1["low"] - 0.4:
            fvg_top = c1["low"]
            fvg_bottom = c3["high"]

            # Did a subsequent candle breach above fvg_top?
            breached = False
            for k in range(i + 2, n - 1):
                if candles[k]["close"] > fvg_top:
                    breached = True
                    break

            # If breached, it becomes an IFVG (Support).
            # Last candle retests this zone from above and rejects:
            if breached and last["open"] >= fvg_top and last["low"] <= fvg_top and last["close"] > fvg_top:
                return TrapResult(
                    trap_type="IFVG_BREAKER",
                    direction="BUY",
                    key_level=fvg_top,
                    sweep_extreme=last["low"],
                    time=last["time"],
                    confidence=0.88,
                    detail=f"SMC Inducement Breached: Bearish FVG di {fvg_top:.2f} jebol dan di-retest sebagai Inverse FVG Support."
                )

    return None
