# AGENTS.md — XAUUSD Signal & Realtime Dashboard

Dokumen panduan standar arsitektur dan pengembangan project `xauusd-signal`.

## Tech Stack
- **Runtime**: Python 3.14+
- **Market Feed**: MetaTrader 5 Python Library (`MetaTrader5`)
- **Backend / Realtime**: FastAPI, Uvicorn, WebSockets (async sub-second polling 150ms)
- **Data & TA**: `pandas`, `numpy`, custom SMC Retail-Trap engine (Sweep, MSS, IFVG)
- **Frontend**: Single-page static HTML + TradingView Lightweight Charts (via CDN, zero build step)
- **Testing**: `pytest`

## Folder Structure
```
xauusd-signal/
├── AGENTS.md                # Project guide for AI agents & contributors
├── config.py                # System settings & trading parameters
├── requirements.txt         # Python dependencies
├── server.py                # FastAPI web server & WebSocket real-time broadcaster
├── core/
│   ├── __init__.py
│   ├── mt5_feed.py          # MT5 bridge: candles, ticks, connection fallback
│   └── smc_engine.py        # Logic: Liquidity sweep, MSS, IFVG, retail traps
├── static/
│   └── index.html           # Realtime TradingView chart & signal dashboard
├── docs/
│   └── specs/               # Technical specs for new features
├── tickets/                 # Task & bug tracking tickets
└── tests/
    ├── __init__.py
    └── test_smc_engine.py   # Unit test for sweep, MSS, and signal generation
```

## Conventions
- **Zero Build Step**: Frontend strictly uses vanilla JS and CDN libraries; do not introduce npm or frontend bundlers without explicit architectural review.
- **Strictly Real Data**: MT5 feed must handle offline status gracefully by returning empty/None with an explicit offline UI banner; no fake or synthetic mock candles permitted.
- **Verification First**: Every logic change in `core/` must be covered by pytest unit tests with explicit assertions.
- **Risk Management**: Signals must include deterministic Stop Loss (SL) and minimum Risk-to-Reward ratio (1:2).

## Verification Commands
Jalankan perintah ini untuk memvalidasi project:
```bash
pytest
```
Menjalankan server web dashboard:
```bash
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
