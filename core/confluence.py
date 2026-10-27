from typing import List, Dict, Optional, Tuple
import pandas as pd
from ta.volatility import AverageTrueRange

from core.traps import TrapResult

def evaluate_macro_trend(
    h4_candles: Optional[List[Dict]],
    ema_period: int = 200,
    atr_period: int = 14
) -> Dict:
    """
    Evaluate H4 Macro Trend bias using EMA and ATR volatility check.
    """
    if not h4_candles or len(h4_candles) < 15:
        return {"bias": "NEUTRAL", "ema": None, "atr_healthy": True}

    df = pd.DataFrame(h4_candles)
    close_series = df["close"]

    # Calculate EMA (adapt span if fewer candles than requested period)
    span = min(ema_period, len(df))
    ema_val = float(close_series.ewm(span=span, adjust=False).mean().iloc[-1])
    last_close = float(close_series.iloc[-1])

    # Calculate ATR
    try:
        atr_indicator = AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=min(atr_period, len(df) - 1)
        )
        atr_series = atr_indicator.average_true_range()
        last_atr = float(atr_series.iloc[-1])
        avg_atr = float(atr_series.tail(20).mean())
        atr_healthy = last_atr >= (0.4 * avg_atr)
    except Exception:
        atr_healthy = True

    if last_close > ema_val:
        bias = "BULLISH"
    elif last_close < ema_val:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "bias": bias,
        "ema": round(ema_val, 2),
        "last_close": round(last_close, 2),
        "atr_healthy": atr_healthy
    }

def score_confluence(
    traps: List[TrapResult],
    h4_candles: Optional[List[Dict]] = None,
    ema_period: int = 200,
    atr_period: int = 14
) -> Tuple[str, bool, int]:
    """
    Score trap confluence:
    - 1 Trap  -> Grade B
    - 2 Traps -> Grade A
    - 3+ Traps -> Grade A+ (if H4 macro-aligned) or Grade A (if capped)
    Returns: (grade, macro_aligned, count)
    """
    count = len(traps)
    if count == 0:
        return ("NONE", False, 0)

    direction = traps[0].direction
    macro_info = evaluate_macro_trend(h4_candles, ema_period, atr_period)

    macro_aligned = False
    if direction == "BUY" and macro_info["bias"] == "BULLISH" and macro_info["atr_healthy"]:
        macro_aligned = True
    elif direction == "SELL" and macro_info["bias"] == "BEARISH" and macro_info["atr_healthy"]:
        macro_aligned = True

    if count == 1:
        grade = "B"
    elif count == 2:
        grade = "A"
    else:
        # 3+ traps
        grade = "A+" if macro_aligned else "A"

    return (grade, macro_aligned, count)
