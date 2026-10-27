import pytest
from core.mt5_feed import MT5Feed

def test_feed_initial_state_and_no_mock():
    # Test feed without connecting
    feed = MT5Feed(symbol="XAUUSD", mode="direct")
    feed.initialize = lambda: False
    feed._connected = False
    assert not feed.is_connected()
    candles = feed.get_candles("M5", 100)
    assert candles == []  # Strictly empty, no mock
    tick = feed.get_latest_tick()
    assert tick is None   # Strictly None, no mock

def test_feed_bridge_mode_offline_graceful():
    # Point to nonexistent bridge
    feed = MT5Feed(symbol="XAUUSD", mode="bridge", bridge_url="http://127.0.0.1:59999")
    connected = feed.initialize()
    assert not connected
    assert not feed.is_connected()
    assert feed.get_candles("M5", 50) == []
    assert feed.get_latest_tick() is None
    feed.shutdown()
