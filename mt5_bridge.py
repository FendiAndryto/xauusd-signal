import os
import logging
from contextlib import asynccontextmanager
from typing import List, Dict

import MetaTrader5 as mt5
from fastapi import FastAPI, HTTPException, Query

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MT5-BRIDGE] %(message)s")
logger = logging.getLogger("mt5-bridge")

SYMBOL = os.getenv("SYMBOL", "XAUUSDm")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8081"))

TF_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
}

connected_to_mt5 = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global connected_to_mt5
    logger.info("Inisialisasi koneksi MetaTrader 5 di Windows host...")
    try:
        if mt5.initialize():
            info = mt5.symbol_info(SYMBOL)
            if info is not None:
                if not info.visible:
                    mt5.symbol_select(SYMBOL, True)
                connected_to_mt5 = True
                logger.info(f"Koneksi MT5 sukses untuk simbol {SYMBOL}.")
            else:
                logger.warning(f"Simbol {SYMBOL} tidak ditemukan di MT5.")
        else:
            logger.warning(f"mt5.initialize() gagal: {mt5.last_error()}")
    except Exception as e:
        logger.error(f"Error saat inisialisasi MT5: {e}")

    yield

    if connected_to_mt5:
        mt5.shutdown()
        connected_to_mt5 = False
        logger.info("MT5 shutdown selesai.")

app = FastAPI(title="MT5 Data Bridge Service", lifespan=lifespan)

@app.get("/status")
async def get_status():
    global connected_to_mt5
    # Cek koneksi aktif
    if connected_to_mt5:
        term_info = mt5.terminal_info()
        if term_info is None or not term_info.connected:
            connected_to_mt5 = False

    return {
        "connected": connected_to_mt5,
        "symbol": SYMBOL
    }

@app.get("/tick")
async def get_tick():
    global connected_to_mt5
    if not connected_to_mt5:
        # Coba inisialisasi ulang jika sempat gagal
        if mt5.initialize() and mt5.symbol_select(SYMBOL, True):
            connected_to_mt5 = True
        else:
            raise HTTPException(status_code=503, detail="MT5 Terminal Disconnected")

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        connected_to_mt5 = False
        raise HTTPException(status_code=503, detail="Gagal mengambil tick dari MT5")

    return {
        "time": int(tick.time),
        "bid": float(tick.bid),
        "ask": float(tick.ask),
        "last": float(tick.last or tick.bid)
    }

@app.get("/candles")
async def get_candles(tf: str = Query("M5"), count: int = 300):
    global connected_to_mt5
    if not connected_to_mt5:
        if mt5.initialize() and mt5.symbol_select(SYMBOL, True):
            connected_to_mt5 = True
        else:
            raise HTTPException(status_code=503, detail="MT5 Terminal Disconnected")

    mt5_tf = TF_MAP.get(tf, mt5.TIMEFRAME_M5)
    rates = mt5.copy_rates_from_pos(SYMBOL, mt5_tf, 0, count)
    if rates is None or len(rates) == 0:
        connected_to_mt5 = False
        raise HTTPException(status_code=503, detail="Gagal mengambil data candle dari MT5")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)
