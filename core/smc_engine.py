from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Signal:
    time: int
    action: str          # "BUY" or "SELL"
    entry_price: float
    sl_price: float
    tp_price: float
    rr_ratio: float
    trap_type: str       # "STOP_HUNT_SWEEP" | "MSS_FVG_CONFIRMATION" | "IFVG_BREAKER"
    reason: str

class SMCEngine:
    def __init__(self, min_rr: float = 2.0, sl_buffer: float = 1.5):
        self.min_rr = min_rr
        self.sl_buffer = sl_buffer

    def find_swings(self, candles: List[Dict], lookback: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """Find swing highs and swing lows from candles."""
        swing_highs = []
        swing_lows = []
        n = len(candles)

        for i in range(lookback, n - lookback):
            current_high = candles[i]["high"]
            current_low = candles[i]["low"]

            # Check if swing high
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

            # Check if swing low
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

    def detect_liquidity_sweep(self, candles: List[Dict], lookback: int = 5) -> Optional[Dict]:
        """
        Detect if the latest completed candle swept a prior swing level and closed back inside.
        """
        if len(candles) < lookback * 2 + 2:
            return None

        swing_highs, swing_lows = self.find_swings(candles[:-1], lookback=lookback)
        last_candle = candles[-1]

        # Check Bearish Sweep (Swept High) -> Potential SELL
        if swing_highs:
            recent_high = swing_highs[-1]
            # Price pierced above the swing high but closed below it
            if last_candle["high"] > recent_high["price"] and last_candle["close"] < recent_high["price"]:
                return {
                    "direction": "SELL",
                    "swept_price": recent_high["price"],
                    "sweep_peak": last_candle["high"],
                    "time": last_candle["time"],
                    "type": "BEARISH_SWEEP"
                }

        # Check Bullish Sweep (Swept Low) -> Potential BUY
        if swing_lows:
            recent_low = swing_lows[-1]
            # Price pierced below the swing low but closed above it
            if last_candle["low"] < recent_low["price"] and last_candle["close"] > recent_low["price"]:
                return {
                    "direction": "BUY",
                    "swept_price": recent_low["price"],
                    "sweep_peak": last_candle["low"],
                    "time": last_candle["time"],
                    "type": "BULLISH_SWEEP"
                }

        return None

    def detect_fvg(self, candles: List[Dict]) -> List[Dict]:
        """Detect Fair Value Gaps in 3-candle patterns."""
        fvgs = []
        if len(candles) < 3:
            return fvgs

        for i in range(len(candles) - 3, len(candles) - 1):
            c1 = candles[i - 1]
            c2 = candles[i]
            c3 = candles[i + 1]

            # Bullish FVG: Low of c3 > High of c1
            if c3["low"] > c1["high"]:
                gap_size = c3["low"] - c1["high"]
                if gap_size > 0.5:
                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "top": c3["low"],
                        "bottom": c1["high"],
                        "time": c2["time"]
                    })

            # Bearish FVG: High of c3 < Low of c1
            elif c3["high"] < c1["low"]:
                gap_size = c1["low"] - c3["high"]
                if gap_size > 0.5:
                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "top": c1["low"],
                        "bottom": c3["high"],
                        "time": c2["time"]
                    })

        return fvgs

    def evaluate(self, candles: List[Dict]) -> Optional[Signal]:
        """
        Evaluate candle series for Retail-Trap / SMC reversal signal.
        """
        if len(candles) < 20:
            return None

        sweep = self.detect_liquidity_sweep(candles, lookback=4)
        if not sweep:
            return None

        last_candle = candles[-1]
        entry_price = round(last_candle["close"], 2)

        if sweep["direction"] == "BUY":
            sl_price = round(sweep["sweep_peak"] - self.sl_buffer, 2)
            risk = entry_price - sl_price
            if risk <= 0.2:
                risk = 1.5
                sl_price = round(entry_price - risk, 2)
            tp_price = round(entry_price + (risk * self.min_rr), 2)
            rr = round((tp_price - entry_price) / risk, 1)

            return Signal(
                time=last_candle["time"],
                action="BUY",
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
                rr_ratio=rr,
                trap_type="STOP_HUNT_SWEEP",
                reason=f"Bandar swept retail low at {sweep['swept_price']:.2f}. Wick rejection confirmed at {entry_price:.2f}."
            )

        elif sweep["direction"] == "SELL":
            sl_price = round(sweep["sweep_peak"] + self.sl_buffer, 2)
            risk = sl_price - entry_price
            if risk <= 0.2:
                risk = 1.5
                sl_price = round(entry_price + risk, 2)
            tp_price = round(entry_price - (risk * self.min_rr), 2)
            rr = round((entry_price - tp_price) / risk, 1)

            return Signal(
                time=last_candle["time"],
                action="SELL",
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
                rr_ratio=rr,
                trap_type="STOP_HUNT_SWEEP",
                reason=f"Bandar swept retail high at {sweep['swept_price']:.2f}. Wick rejection confirmed at {entry_price:.2f}."
            )

        return None
