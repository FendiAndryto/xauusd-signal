import logging
from typing import List, Dict, Optional

try:
    import MetaTrader5 as mt5
    HAS_MT5_LIB = True
except ImportError:
    mt5 = None
    HAS_MT5_LIB = False

import httpx

logger = logging.getLogger("mt5-feed")

TF_MAP = {
    "M1": 1 if not HAS_MT5_LIB else mt5.TIMEFRAME_M1,
    "M5": 5 if not HAS_MT5_LIB else mt5.TIMEFRAME_M5,
    "M15": 15 if not HAS_MT5_LIB else mt5.TIMEFRAME_M15,
    "H1": 16385 if not HAS_MT5_LIB else mt5.TIMEFRAME_H1,
    "H4": 16388 if not HAS_MT5_LIB else mt5.TIMEFRAME_H4,
}

class MT5Feed:
    def __init__(self, symbol: str = "XAUUSD", mode: str = "direct", bridge_url: str = "http://host.docker.internal:8081"):
        self.symbol = symbol
        self.mode = mode.lower()
        self.bridge_url = bridge_url.rstrip("/")
        self._connected = False
        self._http_client: Optional[httpx.Client] = None

        if self.mode == "bridge":
            # ponytail: sync httpx client suffices for local container-to-host bridge (<5ms); upgrade to async if remote
            self._http_client = httpx.Client(timeout=2.0)

    def initialize(self) -> bool:
        """Connect to MT5 directly (Windows) or via HTTP Bridge (Docker/Remote)."""
        if self.mode == "bridge":
            try:
                resp = self._http_client.get(f"{self.bridge_url}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    self._connected = bool(data.get("connected", False))
                    return self._connected
            except Exception as e:
                logger.debug(f"Bridge connection check failed: {e}")
            self._connected = False
            return False

        # Direct Mode (Requires Windows MT5 library)
        if not HAS_MT5_LIB:
            logger.warning("MetaTrader5 library not available on this platform. Use mode='bridge' instead.")
            self._connected = False
            return False

        try:
            if mt5.initialize():
                info = mt5.symbol_info(self.symbol)
                if info is not None:
                    if not info.visible:
                        mt5.symbol_select(self.symbol, True)
                    self._connected = True
                    return True
        except Exception as e:
            logger.error(f"MT5 direct initialize error: {e}")

        self._connected = False
        return False

    def is_connected(self) -> bool:
        return self._connected

    def get_candles(self, timeframe: str = "M5", count: int = 300) -> List[Dict]:
        """
        Fetch real historical candles.
        Returns empty list [] if disconnected or data unavailable. Strictly NO mock data.
        """
        if self.mode == "bridge":
            try:
                resp = self._http_client.get(
                    f"{self.bridge_url}/candles",
                    params={"tf": timeframe, "count": count}
                )
                if resp.status_code == 200:
                    self._connected = True
                    return resp.json()
                self._connected = False
            except Exception:
                self._connected = False
            return []

        # Direct Mode
        if not self._connected and HAS_MT5_LIB:
            self.initialize()

        if self._connected and HAS_MT5_LIB:
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
            # If rates failed, check if MT5 terminal connection dropped
            self._connected = False

        return []

    def get_latest_tick(self) -> Optional[Dict]:
        """
        Fetch latest real price tick.
        Returns None if disconnected or unavailable. Strictly NO mock data.
        """
        if self.mode == "bridge":
            try:
                resp = self._http_client.get(f"{self.bridge_url}/tick")
                if resp.status_code == 200:
                    self._connected = True
                    return resp.json()
                self._connected = False
            except Exception:
                self._connected = False
            return None

        # Direct Mode
        if not self._connected and HAS_MT5_LIB:
            self.initialize()

        if self._connected and HAS_MT5_LIB:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is not None:
                return {
                    "time": int(tick.time),
                    "bid": float(tick.bid),
                    "ask": float(tick.ask),
                    "last": float(tick.last or tick.bid)
                }
            self._connected = False

        return None

    def shutdown(self):
        if self.mode == "bridge" and self._http_client is not None:
            try:
                self._http_client.close()
            except Exception:
                pass
        elif self.mode == "direct" and HAS_MT5_LIB and self._connected:
            try:
                mt5.shutdown()
            except Exception:
                pass
        self._connected = False
