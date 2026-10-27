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

mt5_feed = MT5Feed(symbol=settings.SYMBOL)
smc_engine = SMCEngine(min_rr=settings.MIN_RR, sl_buffer=settings.SL_BUFFER_PIPS)

active_connections: Set[WebSocket] = set()
background_task: asyncio.Task = None
current_tf = "M5"
latest_signals: List[dict] = []

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
    """Background loop polling ticks sub-second (default ~150ms)."""
    poll_interval = settings.POLL_INTERVAL_MS / 1000.0
    last_evaluated_candle_time = 0

    while True:
        try:
            tick = mt5_feed.get_latest_tick()
            await broadcast("tick", {
                "time": tick["time"],
                "bid": tick["bid"],
                "ask": tick["ask"],
                "last": tick["last"]
            })

            # Fetch last 300 candles to monitor structure
            candles = mt5_feed.get_candles(timeframe=current_tf, count=100)
            if candles:
                last_c = candles[-1]
                await broadcast("candle_update", last_c)

                # Check if last candle finished or changed
                if last_c["time"] != last_evaluated_candle_time and len(candles) >= 20:
                    last_evaluated_candle_time = last_c["time"]
                    signal = smc_engine.evaluate(candles)
                    if signal:
                        sig_data = {
                            "time": signal.time,
                            "action": signal.action,
                            "entry_price": signal.entry_price,
                            "sl_price": signal.sl_price,
                            "tp_price": signal.tp_price,
                            "rr_ratio": signal.rr_ratio,
                            "trap_type": signal.trap_type,
                            "reason": signal.reason
                        }
                        latest_signals.append(sig_data)
                        if len(latest_signals) > 50:
                            latest_signals.pop(0)
                        await broadcast("signal", sig_data)
                        logger.info(f"Generated Signal: {sig_data}")

        except Exception as e:
            logger.error(f"Error in tick poller loop: {e}")

        await asyncio.sleep(poll_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MT5 feed connection...")
    connected = mt5_feed.initialize()
    if connected:
        logger.info(f"Connected to MetaTrader 5 terminal for symbol {settings.SYMBOL}")
    else:
        logger.warning("MetaTrader 5 terminal not found or offline. Running with realistic synthetic feed.")

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
    return mt5_feed.get_candles(timeframe=tf, count=count)

@app.get("/api/status")
async def get_status():
    return {
        "symbol": settings.SYMBOL,
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
                "timeframe": current_tf,
                "recent_signals": latest_signals[-5:]
            }
        }))
        while True:
            # Keep connection open & handle incoming client messages (e.g. switch TF)
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                if msg.get("action") == "set_timeframe":
                    new_tf = msg.get("timeframe", "M5")
                    current_tf = new_tf
                    candles = mt5_feed.get_candles(timeframe=new_tf, count=300)
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
