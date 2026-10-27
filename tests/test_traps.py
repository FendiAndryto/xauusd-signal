import pytest
from datetime import datetime, timezone

from core.traps import (
    TrapResult,
    detect_sweep,
    detect_asian_judas,
    detect_ifvg_breaker,
    detect_equal_levels,
    detect_rsi_divergence
)
from core.confluence import score_confluence
from core.smc_engine import SMCEngine

def make_candle(idx: int, op: float, hi: float, lo: float, cl: float, base_time: int = 1700000000):
    return {
        "time": base_time + idx * 300,
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "volume": 500
    }

def test_trap_sweep():
    candles = [make_candle(i, 2600, 2605, 2595, 2600) for i in range(10)]
    # Swing high at 2615
    candles.append(make_candle(10, 2600, 2615, 2598, 2608))
    for i in range(11, 16):
        candles.append(make_candle(i, 2605, 2610, 2600, 2604))
    # Sweep candle: high 2618 > 2615, close 2612 < 2615
    candles.append(make_candle(16, 2604, 2618, 2602, 2612))

    trap = detect_sweep(candles, lookback=4)
    assert trap is not None
    assert trap.trap_type == "STOP_HUNT_SWEEP"
    assert trap.direction == "SELL"
    assert trap.key_level == 2615
    assert trap.sweep_extreme == 2618

def test_trap_asian_judas():
    # Base timestamp: 2026-10-27 00:00:00 UTC
    base_utc = int(datetime(2026, 10, 27, 0, 0, tzinfo=timezone.utc).timestamp())

    # Build Asian session candles (00:00 - 05:30 UTC): 20 candles
    candles = []
    for i in range(20):
        candles.append(make_candle(i, 2650, 2655, 2645, 2650, base_time=base_utc))
    # Asian High at index 5: 2660
    candles[5] = make_candle(5, 2650, 2660, 2648, 2655, base_time=base_utc)

    # Move to London open (08:00 UTC = 8 * 3600 = 28800s)
    london_time = base_utc + 28800
    for i in range(20, 25):
        candles.append(make_candle(i - 20, 2652, 2658, 2650, 2656, base_time=london_time - 1500))

    # Trigger candle at 08:00 UTC sweeps Asian high (2664 > 2660) and closes at 2657 < 2660
    trigger_candle = {
        "time": london_time,
        "open": 2656.0,
        "high": 2664.0,
        "low": 2654.0,
        "close": 2657.0,
        "volume": 1200
    }
    candles.append(trigger_candle)

    trap = detect_asian_judas(candles, asian_hours=(0, 6), london_hours=(7, 10))
    assert trap is not None
    assert trap.trap_type == "ASIAN_JUDAS"
    assert trap.direction == "SELL"
    assert trap.key_level == 2660
    assert trap.sweep_extreme == 2664

def test_trap_ifvg_breaker():
    candles = []
    # Baseline
    for i in range(10):
        candles.append(make_candle(i, 2650, 2652, 2648, 2650))

    # Form a Bullish FVG: c1 high = 2652, c3 low = 2658 (gap between 2652 and 2658)
    candles.append(make_candle(10, 2650, 2652, 2648, 2651))  # c1: high 2652
    candles.append(make_candle(11, 2651, 2665, 2650, 2664))  # c2: big up
    candles.append(make_candle(12, 2664, 2668, 2658, 2666))  # c3: low 2658

    # Breach it: candle closes below 2652
    candles.append(make_candle(13, 2660, 2661, 2649, 2648))  # close 2648 < 2652 (breached)
    candles.append(make_candle(14, 2648, 2650, 2645, 2647))

    # Retest and reject: high touches 2653 (>= 2652) but closes at 2649 (< 2652)
    retest_candle = make_candle(15, 2647, 2653, 2646, 2649)
    candles.append(retest_candle)

    trap = detect_ifvg_breaker(candles, max_age=20)
    assert trap is not None
    assert trap.trap_type == "IFVG_BREAKER"
    assert trap.direction == "SELL"
    assert trap.key_level == 2652

def test_trap_equal_levels():
    candles = []
    for i in range(10):
        candles.append(make_candle(i, 2640, 2644, 2638, 2640))

    # Swing high 1 at index 10: 2660.0
    candles.append(make_candle(10, 2640, 2660.0, 2638, 2655))
    for i in range(11, 18):
        candles.append(make_candle(i, 2650, 2654, 2645, 2648))

    # Swing high 2 at index 18: 2660.2 (EQH within 1.5 pips, gap 8 bars)
    candles.append(make_candle(18, 2648, 2660.2, 2646, 2654))
    for i in range(19, 26):
        candles.append(make_candle(i, 2652, 2656, 2648, 2650))

    # Sweep candle: pierces 2662 > 2660.2, closes at 2658 < 2660.0
    candles.append(make_candle(26, 2650, 2662.0, 2648, 2658.0))

    trap = detect_equal_levels(candles, tolerance_pips=1.5, min_gap=5)
    assert trap is not None
    assert trap.trap_type == "EQH_EQL"
    assert trap.direction == "SELL"
    assert trap.sweep_extreme == 2662.0

def test_confluence_grading():
    t1 = TrapResult("STOP_HUNT_SWEEP", "BUY", 2630.0, 2627.0, 1700000000, 0.85, "detail 1")
    t2 = TrapResult("EQH_EQL", "BUY", 2630.0, 2626.5, 1700000000, 0.90, "detail 2")
    t3 = TrapResult("IFVG_BREAKER", "BUY", 2630.0, 2627.5, 1700000000, 0.88, "detail 3")

    # Grade B: 1 trap
    grade_b, _, _ = score_confluence([t1], None)
    assert grade_b == "B"

    # Grade A: 2 traps
    grade_a, _, _ = score_confluence([t1, t2], None)
    assert grade_a == "A"

    # Grade A+ requires 3+ traps and macro alignment
    # Mock H4 candles with bullish trend (close > EMA 200)
    h4_candles = [{"time": 1700000000 + i * 14400, "open": 2600 + i, "high": 2605 + i, "low": 2595 + i, "close": 2602 + i} for i in range(30)]
    grade_aplus, aligned, count = score_confluence([t1, t2, t3], h4_candles)
    assert count == 3
    assert aligned is True
    assert grade_aplus == "A+"

def test_trap_rsi_divergence():
    candles = []
    # Build strong uptrend to pump RSI > 65
    price = 2600.0
    for i in range(25):
        price += 2.0
        candles.append(make_candle(i, price - 1, price + 1, price - 2, price))

    # Swing high 1 at index 25 (price around 2650)
    swing_high_price = price + 5.0
    candles.append(make_candle(25, price, swing_high_price, price - 1, swing_high_price - 1))

    # Pullback candles
    p = swing_high_price - 2.0
    for i in range(26, 33):
        p -= 1.0
        candles.append(make_candle(i, p + 0.2, p + 0.5, p - 1.0, p))

    # Trigger candle: higher high in price (2658 > 2655), but bearish close rejection
    trigger = make_candle(33, p, swing_high_price + 3.0, p - 1.0, p - 0.5)
    candles.append(trigger)

    trap = detect_rsi_divergence(candles, rsi_period=14, ob_threshold=60.0, os_threshold=40.0)
    assert trap is not None
    assert trap.trap_type == "RSI_DIV_SWEEP"
    assert trap.direction == "SELL"
    assert trap.sweep_extreme == swing_high_price + 3.0

def test_directional_guard_conflict(monkeypatch):
    engine = SMCEngine()
    candles = [make_candle(i, 2650, 2652, 2648, 2650) for i in range(25)]

    t_buy = TrapResult("STOP_HUNT_SWEEP", "BUY", 2640.0, 2635.0, 1700000000, 0.85, "buy trap")
    t_sell = TrapResult("EQH_EQL", "SELL", 2660.0, 2665.0, 1700000000, 0.90, "sell trap")

    monkeypatch.setattr("core.smc_engine.detect_sweep", lambda c: t_buy)
    monkeypatch.setattr("core.smc_engine.detect_equal_levels", lambda c, tolerance_pips, min_gap: t_sell)

    res = engine.evaluate(candles)
    # Must reject conflicting traps and return None
    assert res is None
