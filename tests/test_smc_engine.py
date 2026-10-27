import pytest
from core.smc_engine import SMCEngine, Signal

def create_mock_candle(time_idx: int, op: float, hi: float, lo: float, cl: float):
    return {
        "time": 1700000000 + time_idx * 300,
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "volume": 500
    }

def test_find_swings():
    engine = SMCEngine()
    candles = [
        create_mock_candle(0, 2600, 2605, 2595, 2602),
        create_mock_candle(1, 2602, 2610, 2600, 2608),
        create_mock_candle(2, 2608, 2625, 2605, 2620),  # Swing High at index 2 (price 2625)
        create_mock_candle(3, 2620, 2615, 2600, 2605),
        create_mock_candle(4, 2605, 2608, 2580, 2585),  # Swing Low at index 4 (price 2580)
        create_mock_candle(5, 2585, 2600, 2584, 2595),
        create_mock_candle(6, 2595, 2605, 2590, 2600),
    ]
    highs, lows = engine.find_swings(candles, lookback=2)
    assert len(highs) >= 1
    assert any(h["price"] == 2625 for h in highs)
    assert len(lows) >= 1
    assert any(l["price"] == 2580 for l in lows)

def test_detect_bearish_sweep():
    engine = SMCEngine()
    candles = []
    # Base candles around 2650
    for i in range(10):
        candles.append(create_mock_candle(i, 2648, 2652, 2646, 2650))
    # Create clear swing high at index 10: high = 2660
    candles.append(create_mock_candle(10, 2650, 2660, 2649, 2655))
    for i in range(11, 16):
        candles.append(create_mock_candle(i, 2655 - (i - 10), 2656, 2645, 2650))

    # Trigger candle sweeps high (2663 > 2660) but closes below (2658 < 2660)
    sweep_candle = create_mock_candle(16, 2650, 2663, 2648, 2658)
    candles.append(sweep_candle)

    sweep = engine.detect_liquidity_sweep(candles, lookback=4)
    assert sweep is not None
    assert sweep["direction"] == "SELL"
    assert sweep["swept_price"] == 2660
    assert sweep["sweep_peak"] == 2663

def test_detect_bullish_sweep():
    engine = SMCEngine()
    candles = []
    for i in range(10):
        candles.append(create_mock_candle(i, 2650, 2654, 2648, 2650))
    # Create clear swing low at index 10: low = 2640
    candles.append(create_mock_candle(10, 2650, 2652, 2640, 2644))
    for i in range(11, 16):
        candles.append(create_mock_candle(i, 2645 + (i - 10), 2655, 2644, 2650))

    # Trigger candle sweeps low (2637 < 2640) but closes above (2643 > 2640)
    sweep_candle = create_mock_candle(16, 2648, 2650, 2637, 2643)
    candles.append(sweep_candle)

    sweep = engine.detect_liquidity_sweep(candles, lookback=4)
    assert sweep is not None
    assert sweep["direction"] == "BUY"
    assert sweep["swept_price"] == 2640
    assert sweep["sweep_peak"] == 2637

def test_signal_generation_and_risk_reward():
    engine = SMCEngine(min_rr=2.0, sl_buffer=1.0)
    candles = []
    for i in range(10):
        candles.append(create_mock_candle(i, 2650, 2655, 2645, 2650))
    # Swing low at 2635
    candles.append(create_mock_candle(10, 2650, 2652, 2635, 2640))
    for i in range(11, 19):
        candles.append(create_mock_candle(i, 2642, 2648, 2640, 2645))

    # Sweeps low to 2632, closes back at 2638
    candles.append(create_mock_candle(19, 2645, 2646, 2632, 2638))

    signal = engine.evaluate(candles)
    assert signal is not None
    assert isinstance(signal, Signal)
    assert signal.action == "BUY"
    assert signal.entry_price == 2638
    assert signal.sl_price < signal.entry_price  # SL below entry
    assert signal.tp_price > signal.entry_price  # TP above entry
    assert signal.rr_ratio >= 2.0                # Min RR 1:2
