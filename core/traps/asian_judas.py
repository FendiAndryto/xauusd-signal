from datetime import datetime, timezone
from typing import List, Dict, Optional
from . import TrapResult

def detect_asian_judas(
    candles: List[Dict],
    asian_hours: tuple = (0, 6),
    london_hours: tuple = (7, 10),
    tolerance_pips: float = 0.5
) -> Optional[TrapResult]:
    """
    Detect Judas Swing on Asian Session High/Low during London Open.
    Asian session: 00:00 - 06:00 UTC
    London trigger window: 07:00 - 10:00 UTC
    """
    if len(candles) < 20:
        return None

    last = candles[-1]
    last_dt = datetime.fromtimestamp(last["time"], timezone.utc)

    # Trigger window must be London Open
    if not (london_hours[0] <= last_dt.hour < london_hours[1]):
        return None

    # Filter candles that belong to the Asian session of the same UTC day
    asian_candles = []
    for c in candles[:-1]:
        c_dt = datetime.fromtimestamp(c["time"], timezone.utc)
        if c_dt.date() == last_dt.date() and (asian_hours[0] <= c_dt.hour < asian_hours[1]):
            asian_candles.append(c)

    if len(asian_candles) < 5:
        return None

    asian_high = max(c["high"] for c in asian_candles)
    asian_low = min(c["low"] for c in asian_candles)

    if asian_high <= asian_low or (asian_high - asian_low) < tolerance_pips:
        return None

    # Bearish Judas: sweeps above Asian High then closes back below
    if last["high"] > asian_high and last["close"] < asian_high:
        return TrapResult(
            trap_type="ASIAN_JUDAS",
            direction="SELL",
            key_level=asian_high,
            sweep_extreme=last["high"],
            time=last["time"],
            confidence=0.90,
            detail=f"London Judas Swing sweep Asian High {asian_high:.2f} (ekor ke {last['high']:.2f}) lalu reject balik."
        )

    # Bullish Judas: sweeps below Asian Low then closes back above
    if last["low"] < asian_low and last["close"] > asian_low:
        return TrapResult(
            trap_type="ASIAN_JUDAS",
            direction="BUY",
            key_level=asian_low,
            sweep_extreme=last["low"],
            time=last["time"],
            confidence=0.90,
            detail=f"London Judas Swing sweep Asian Low {asian_low:.2f} (ekor ke {last['low']:.2f}) lalu reject balik."
        )

    return None
