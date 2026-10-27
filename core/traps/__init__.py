from dataclasses import dataclass
from typing import Optional

@dataclass
class TrapResult:
    trap_type: str        # "STOP_HUNT_SWEEP" | "ASIAN_JUDAS" | "IFVG_BREAKER" | "EQH_EQL" | "RSI_DIV_SWEEP"
    direction: str        # "BUY" | "SELL"
    key_level: float      # price level that trapped retail
    sweep_extreme: float  # furthest price reached by wick
    time: int             # timestamp of the trigger candle
    confidence: float     # 0.0 - 1.0
    detail: str           # Human readable explanation

from .sweep import detect_sweep
from .asian_judas import detect_asian_judas
from .ifvg_breaker import detect_ifvg_breaker
from .equal_levels import detect_equal_levels
from .rsi_divergence import detect_rsi_divergence

__all__ = [
    "TrapResult",
    "detect_sweep",
    "detect_asian_judas",
    "detect_ifvg_breaker",
    "detect_equal_levels",
    "detect_rsi_divergence",
]
