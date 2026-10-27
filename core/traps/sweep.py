from typing import List, Dict, Optional, Tuple
from . import TrapResult

def find_swings(candles: List[Dict], lookback: int = 4) -> Tuple[List[Dict], List[Dict]]:
    swing_highs = []
    swing_lows = []
    n = len(candles)

    for i in range(lookback, n - lookback):
        current_high = candles[i]["high"]
        current_low = candles[i]["low"]

        is_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j]["high"] >= current_high:
                is_high = False
                break
        if is_high:
            swing_highs.append({
                "index": i,
                "time": candles[i]["time"],
                "price": current_high,
                "candle": candles[i]
            })

        is_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j]["low"] <= current_low:
                is_low = False
                break
        if is_low:
            swing_lows.append({
                "index": i,
                "time": candles[i]["time"],
                "price": current_low,
                "candle": candles[i]
            })

    return swing_highs, swing_lows

def detect_sweep(candles: List[Dict], lookback: int = 4) -> Optional[TrapResult]:
    """Detect classic stop hunt sweep on prior swing high or low."""
    if len(candles) < lookback * 2 + 2:
        return None

    swing_highs, swing_lows = find_swings(candles[:-1], lookback=lookback)
    last = candles[-1]

    # Bearish sweep (swept high) -> SELL
    if swing_highs:
        recent_high = swing_highs[-1]
        if last["high"] > recent_high["price"] and last["close"] < recent_high["price"]:
            return TrapResult(
                trap_type="STOP_HUNT_SWEEP",
                direction="SELL",
                key_level=recent_high["price"],
                sweep_extreme=last["high"],
                time=last["time"],
                confidence=0.85,
                detail=f"Stop hunt sweep di swing high {recent_high['price']:.2f}. Jarum ke {last['high']:.2f} lalu close kembali di bawah."
            )

    # Bullish sweep (swept low) -> BUY
    if swing_lows:
        recent_low = swing_lows[-1]
        if last["low"] < recent_low["price"] and last["close"] > recent_low["price"]:
            return TrapResult(
                trap_type="STOP_HUNT_SWEEP",
                direction="BUY",
                key_level=recent_low["price"],
                sweep_extreme=last["low"],
                time=last["time"],
                confidence=0.85,
                detail=f"Stop hunt sweep di swing low {recent_low['price']:.2f}. Jarum ke {last['low']:.2f} lalu close kembali di atas."
            )

    return None
