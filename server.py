import asyncio
import json
import logging
from typing import List, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from core.mt5_feed import MT5Feed
from core.smc_engine import SMCEngine, Signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xauusd-server")

mt5_feed = MT5Feed(
    symbol=settings.SYMBOL,
    mode=settings.MT5_MODE,
    bridge_url=settings.MT5_BRIDGE_URL
)
smc_engine = SMCEngine(min_rr=settings.MIN_RR, sl_buffer=settings.SL_BUFFER_PIPS)

active_connections: Set[WebSocket] = set()
background_task: asyncio.Task = None
current_tf = "M5"
latest_signals: List[dict] = []
last_connection_state: bool = False

async def broadcast(event_type: str, data: dict):
    if not active_connections:
        return
    message = json.dumps({"event": event_type, "data": data})
    disconnected = set()
    for ws in active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        active_connections.discard(ws)

async def tick_poller_loop():
    """Background loop polling real MT5 ticks sub-second (default ~150ms)."""
    global last_connection_state
    poll_interval = settings.POLL_INTERVAL_MS / 1000.0
    last_evaluated_candle_time = 0
    candle_sync_counter = 0

    while True:
        try:
            tick = await asyncio.to_thread(mt5_feed.get_latest_tick)

            # Broadcast connection state transition
            is_connected = mt5_feed.is_connected()
            if is_connected != last_connection_state:
                last_connection_state = is_connected
                await broadcast("status", {
                    "connected": is_connected,
                    "symbol": settings.SYMBOL,
                    "mode": settings.MT5_MODE
                })

            if tick is not None:
                await broadcast("tick", {
                    "time": tick["time"],
                    "bid": tick["bid"],
                    "ask": tick["ask"],
                    "last": tick["last"]
                })

                # Sync candle structure periodically (~every 1s) to conserve CPU/network
                candle_sync_counter += 1
                if candle_sync_counter >= max(1, int(1.0 / poll_interval)):
                    candle_sync_counter = 0
                    candles = await asyncio.to_thread(mt5_feed.get_candles, current_tf, 300)
                    if candles:
                        last_c = candles[-1]
                        await broadcast("candle_update", last_c)

                        # Evaluate structure using completed bars (candles[:-1]) on bar close
                        if last_c["time"] != last_evaluated_candle_time and len(candles) >= 20:
                            last_evaluated_candle_time = last_c["time"]
                            # Fetch H4 candles for macro trend filter (>=200 candles for EMA 200)
                            h4_candles = await asyncio.to_thread(mt5_feed.get_candles, "H4", 250)
                            signal = smc_engine.evaluate(candles[:-1], h4_candles)
                            if signal:
                                sig_data = {
                                    "time": signal.time,
                                    "action": signal.action,
                                    "entry_price": signal.entry_price,
                                    "sl_price": signal.sl_price,
                                    "tp_price": signal.tp_price,
                                    "rr_ratio": signal.rr_ratio,
                                    "grade": signal.grade,
                                    "traps": signal.traps,
                                    "trap_type": signal.trap_type,
                                    "confluence_score": signal.confluence_score,
                                    "macro_aligned": signal.macro_aligned,
                                    "reason": signal.reason
                                }
                                latest_signals.append(sig_data)
                                if len(latest_signals) > 50:
                                    latest_signals.pop(0)
                                await broadcast("signal", sig_data)
                                logger.info(f"Generated Confluence Signal: Grade {signal.grade} {sig_data}")

        except Exception as e:
            logger.error(f"Error in tick poller loop: {e}")

        await asyncio.sleep(poll_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting MT5 feed connection (mode={settings.MT5_MODE})...")
    connected = mt5_feed.initialize()
    if connected:
        logger.info(f"Connected to MetaTrader 5 for symbol {settings.SYMBOL}")
    else:
        logger.warning("MetaTrader 5 terminal/bridge offline. Waiting for real MT5 connection...")

    global background_task
    background_task = asyncio.create_task(tick_poller_loop())
    yield
    # Shutdown
    if background_task:
        background_task.cancel()
    mt5_feed.shutdown()
    logger.info("Feed and server shutdown completed.")

app = FastAPI(title="XAUUSD Retail-Trap Signal Server", lifespan=lifespan)

@app.get("/api/candles")
async def get_candles(tf: str = Query("M5"), count: int = 300):
    global current_tf
    current_tf = tf
    return await asyncio.to_thread(mt5_feed.get_candles, tf, count)

@app.get("/api/status")
async def get_status():
    return {
        "symbol": settings.SYMBOL,
        "mode": settings.MT5_MODE,
        "connected_to_mt5": mt5_feed.is_connected(),
        "poll_interval_ms": settings.POLL_INTERVAL_MS,
        "current_tf": current_tf,
        "recent_signals": latest_signals[-10:]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_tf
    await websocket.accept()
    active_connections.add(websocket)
    try:
        # Initial greeting with state
        await websocket.send_text(json.dumps({
            "event": "connected",
            "data": {
                "symbol": settings.SYMBOL,
                "connected_to_mt5": mt5_feed.is_connected(),
                "mode": settings.MT5_MODE,
                "timeframe": current_tf,
                "recent_signals": latest_signals[-5:]
            }
        }))
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                if msg.get("action") == "set_timeframe":
                    new_tf = msg.get("timeframe", "M5")
                    current_tf = new_tf
                    candles = await asyncio.to_thread(mt5_feed.get_candles, new_tf, 300)
                    await websocket.send_text(json.dumps({
                        "event": "candles_snapshot",
                        "data": {"timeframe": new_tf, "candles": candles}
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        active_connections.discard(websocket)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
