import time
import random
from typing import List, Dict, Optional
import MetaTrader5 as mt5

TF_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
}

TF_SECONDS = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "H1": 3600,
}

class MT5Feed:
    def __init__(self, symbol: str = "XAUUSD"):
        self.symbol = symbol
        self._connected = False
        self._mock_base_price = 2650.0
        self._mock_candles: Dict[str, List[Dict]] = {}
        self._mock_last_tick = self._mock_base_price

    def initialize(self) -> bool:
        """Attempt to connect to MetaTrader 5 terminal."""
        try:
            if mt5.initialize():
                # Check symbol exists
                info = mt5.symbol_info(self.symbol)
                if info is not None:
                    if not info.visible:
                        mt5.symbol_select(self.symbol, True)
                    self._connected = True
                    return True
        except Exception:
            pass
        self._connected = False
        return False

    def is_connected(self) -> bool:
        return self._connected

    def get_candles(self, timeframe: str = "M5", count: int = 300) -> List[Dict]:
        """Fetch historical candles formatted for TradingView Lightweight Charts."""
        if self._connected:
            tf = TF_MAP.get(timeframe, mt5.TIMEFRAME_M5)
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            if rates is not None and len(rates) > 0:
                result = []
                for r in rates:
                    result.append({
                        "time": int(r['time']),
                        "open": float(r['open']),
                        "high": float(r['high']),
                        "low": float(r['low']),
                        "close": float(r['close']),
                        "volume": int(r['tick_volume'])
                    })
                return result

        # Mock fallback if MT5 not connected
        return self._generate_mock_candles(timeframe, count)

    def get_latest_tick(self) -> Dict:
        """Fetch latest price tick."""
        now = int(time.time())
        if self._connected:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is not None:
                return {
                    "time": int(tick.time),
                    "bid": float(tick.bid),
                    "ask": float(tick.ask),
                    "last": float(tick.last or tick.bid)
                }

        # Mock tick walk
        delta = (random.random() - 0.495) * 0.4
        self._mock_last_tick = round(self._mock_last_tick + delta, 2)
        return {
            "time": now,
            "bid": round(self._mock_last_tick - 0.25, 2),
            "ask": round(self._mock_last_tick + 0.25, 2),
            "last": self._mock_last_tick
        }

    def _generate_mock_candles(self, timeframe: str, count: int) -> List[Dict]:
        """Generate realistic synthetic historical candles."""
        tf_sec = TF_SECONDS.get(timeframe, 300)
        now = int(time.time())
        aligned_now = now - (now % tf_sec)

        candles = []
        curr = self._mock_base_price
        for i in range(count, 0, -1):
            c_time = aligned_now - (i * tf_sec)
            op = curr
            change = (random.random() - 0.49) * 4.0
            cl = round(op + change, 2)
            hi = round(max(op, cl) + random.random() * 2.5, 2)
            lo = round(min(op, cl) - random.random() * 2.5, 2)
            candles.append({
                "time": c_time,
                "open": op,
                "high": hi,
                "low": lo,
                "close": cl,
                "volume": random.randint(100, 2000)
            })
            curr = cl

        self._mock_last_tick = curr
        return candles

    def shutdown(self):
        if self._connected:
            try:
                mt5.shutdown()
            except Exception:
                pass
            self._connected = False
