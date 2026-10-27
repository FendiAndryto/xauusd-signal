from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from config import settings
from core.traps import (
    TrapResult,
    detect_sweep,
    detect_asian_judas,
    detect_ifvg_breaker,
    detect_equal_levels,
    detect_rsi_divergence
)
from core.confluence import score_confluence

@dataclass
class Signal:
    time: int
    action: str           # "BUY" or "SELL"
    entry_price: float
    sl_price: float
    tp_price: float
    rr_ratio: float
    grade: str            # "B" | "A" | "A+"
    traps: List[str]      # List of triggered trap types
    trap_type: str        # Primary trap type (backward compatibility)
    reason: str
    confluence_score: int
    macro_aligned: bool

class SMCEngine:
    def __init__(self, min_rr: float = 2.0, sl_buffer: float = 1.5):
        self.min_rr = min_rr
        self.sl_buffer = sl_buffer

    def find_swings(self, candles: List[Dict], lookback: int = 5) -> Tuple[List[Dict], List[Dict]]:
        from core.traps.sweep import find_swings as _find_swings
        return _find_swings(candles, lookback=lookback)

    def detect_liquidity_sweep(self, candles: List[Dict], lookback: int = 5) -> Optional[Dict]:
        trap = detect_sweep(candles, lookback=lookback)
        if trap:
            return {
                "direction": trap.direction,
                "swept_price": trap.key_level,
                "sweep_peak": trap.sweep_extreme,
                "time": trap.time,
                "type": "BULLISH_SWEEP" if trap.direction == "BUY" else "BEARISH_SWEEP"
            }
        return None

    def evaluate(self, candles: List[Dict], h4_candles: Optional[List[Dict]] = None) -> Optional[Signal]:
        """
        Evaluate candle series against 5 retail trap patterns and score confluence.
        """
        if len(candles) < 20:
            return None

        active_traps: List[TrapResult] = []

        # 1. Standard Swing Liquidity Sweep
        t_sweep = detect_sweep(candles)
        if t_sweep:
            active_traps.append(t_sweep)

        # 2. Asian Range Judas Swing (Time & Session Trap)
        t_judas = detect_asian_judas(
            candles,
            asian_hours=settings.ASIAN_SESSION_UTC,
            london_hours=settings.LONDON_OPEN_UTC,
            tolerance_pips=settings.SWEEP_TOLERANCE_PIPS
        )
        if t_judas:
            active_traps.append(t_judas)

        # 3. SMC Inducement & Inverse FVG (IFVG Breaker)
        t_ifvg = detect_ifvg_breaker(candles, max_age=settings.IFVG_MAX_AGE_CANDLES)
        if t_ifvg:
            active_traps.append(t_ifvg)

        # 4. Equal Highs / Equal Lows (EQH/EQL Double Top/Bottom Sweep)
        t_eql = detect_equal_levels(
            candles,
            tolerance_pips=settings.EQL_TOLERANCE_PIPS,
            min_gap=settings.EQL_MIN_GAP_CANDLES
        )
        if t_eql:
            active_traps.append(t_eql)

        # 5. RSI Divergence Secondary Sweep
        t_rsi = detect_rsi_divergence(
            candles,
            rsi_period=settings.RSI_PERIOD,
            ob_threshold=settings.RSI_OVERBOUGHT,
            os_threshold=settings.RSI_OVERSOLD
        )
        if t_rsi:
            active_traps.append(t_rsi)

        if not active_traps:
            return None

        # Directional Guard: All active traps must agree on direction
        directions = {t.direction for t in active_traps}
        if len(directions) > 1:
            return None  # Conflicting directional signals -> discard

        direction = active_traps[0].direction
        last_candle = candles[-1]
        entry_price = round(last_candle["close"], 2)

        # Score Confluence & Macro Trend
        grade, macro_aligned, count = score_confluence(
            active_traps,
            h4_candles,
            ema_period=settings.EMA_PERIOD,
            atr_period=settings.ATR_PERIOD
        )

        # Compute Stop Loss & Take Profit from outermost sweep extreme
        if direction == "BUY":
            min_extreme = min(t.sweep_extreme for t in active_traps)
            sl_price = round(min_extreme - self.sl_buffer, 2)
            risk = entry_price - sl_price
            if risk > settings.MAX_SL_PIPS:
                risk = settings.MAX_SL_PIPS
                sl_price = round(entry_price - risk, 2)
            elif risk < 0.5:
                risk = 1.5
                sl_price = round(entry_price - risk, 2)
            tp_price = round(entry_price + (risk * self.min_rr), 2)
            rr = round((tp_price - entry_price) / risk, 1)

        else:  # SELL
            max_extreme = max(t.sweep_extreme for t in active_traps)
            sl_price = round(max_extreme + self.sl_buffer, 2)
            risk = sl_price - entry_price
            if risk > settings.MAX_SL_PIPS:
                risk = settings.MAX_SL_PIPS
                sl_price = round(entry_price + risk, 2)
            elif risk < 0.5:
                risk = 1.5
                sl_price = round(entry_price + risk, 2)
            tp_price = round(entry_price - (risk * self.min_rr), 2)
            rr = round((entry_price - tp_price) / risk, 1)

        trap_names = [t.trap_type for t in active_traps]
        primary_trap = active_traps[0].trap_type
        narrative = " + ".join(t.detail for t in active_traps)

        return Signal(
            time=last_candle["time"],
            action=direction,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            rr_ratio=rr,
            grade=grade,
            traps=trap_names,
            trap_type=primary_trap,
            reason=narrative,
            confluence_score=count,
            macro_aligned=macro_aligned
        )
