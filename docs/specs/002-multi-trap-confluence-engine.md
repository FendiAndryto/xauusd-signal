# SPEC-002: Multi-Trap Confluence Engine

## Goal
Mengembangkan Multi-Trap Confluence Engine untuk mendeteksi 5 pola jebakan likuiditas retail (Stop Hunt Sweep, Asian Range Judas Swing, SMC IFVG Inducement Breaker, Equal Highs/Lows Trap, dan RSI Divergence Secondary Sweep) yang dilengkapi dengan sistem penilaian konfluensi (Grade B, A, A+) dan filter macro trend H4.

## Requirements
1. **5 Modular Trap Detectors**:
   - `SWEEP`: Stop hunt klasik pada swing high/low dengan penolakan ekor (wick rejection).
   - `ASIAN_JUDAS`: Breakout palsu batas High/Low sesi Asia (00:00–06:00 UTC) pada awal sesi London (07:00–10:00 UTC).
   - `IFVG_BREAKER`: FVG retail pertama yang berhasil ditembus penuh (invalidated) dan di-retest dari sisi berlawanan sebagai Inverse FVG.
   - `EQH_EQL`: Sapuan likuiditas di atas/bawah swing point kembar (selisih < 1.5 pip, jarak minimal 5 candle).
   - `RSI_DIV_SWEEP`: Secondary sweep pada harga ekstrem bersamaan dengan kondisi overbought (>70) atau oversold (<30) RSI divergence.
2. **Directional Safety Guard**: Jika terdeteksi sinyal trap dengan arah berlawanan (misal 1 Buy dan 1 Sell), batalkan sinyal (no trade).
3. **Confluence Grading**:
   - **Grade B**: Terdeteksi 1 trap valid.
   - **Grade A**: Terdeteksi 2 trap searah.
   - **Grade A+**: Terdeteksi 3+ trap searah DAN selaras dengan filter macro H4 (Buy > EMA 200, Sell < EMA 200, ATR sehat).
   - Jika 3+ trap tetapi tidak selaras dengan macro H4, grade dibatasi maksimal Grade A.
4. **Deterministic Risk Parameters**:
   - SL dihitung dari level ekor sweep paling ekstrem di antara semua trap yang berkontribusi + buffer 2 pip.
   - Minimal Risk-to-Reward (RR) 1:2.0.
5. **UI Enrichment**: Dashboard menampilkan badge Grade (B kuning, A biru, A+ hijau), pill badge untuk setiap trap yang terpicu, dan indikator keselarasan macro.

## Impact Analysis (Files Touched)
- `config.py`: Penambahan parameter EMA_PERIOD, ATR_PERIOD, EQL_TOLERANCE_PIPS, RSI_PERIOD, dll.
- `core/traps/` *(Direktori baru)*:
  - `core/traps/__init__.py`
  - `core/traps/sweep.py`
  - `core/traps/asian_judas.py`
  - `core/traps/ifvg_breaker.py`
  - `core/traps/equal_levels.py`
  - `core/traps/rsi_divergence.py`
- `core/confluence.py` *(Baru)*: Kalkulator scoring konfluensi & filter macro H4 EMA/ATR.
- `core/smc_engine.py`: Refactor orchestrator `evaluate()`, integrasi TrapResult & Signal model baru.
- `core/mt5_feed.py`: Tambah mapping timeframe `"H4"`.
- `server.py`: Fetch candle H4 berkala, broadcast data sinyal yang diperkaya.
- `static/index.html`: Render badge grade, pill tag trap, dan status macro.
- `tests/test_traps.py` *(Baru)*: Unit test komprehensif untuk setiap detektor trap dan sistem grading.

## Acceptance Criteria
- [ ] AC1: Kelima detektor trap teruji secara independen dengan unit test sintetis di `tests/test_traps.py`.
- [ ] AC2: Jika terdapat konflik arah (BUY vs SELL), engine mengembalikan `None`.
- [ ] AC3: Grade B, A, dan A+ terhitung sesuai jumlah trap dan status keselarasan macro H4.
- [ ] AC4: Stop loss memperhitungkan level ekstrem terluar dari seluruh trap yang terpicu.
- [ ] AC5: Server FastAPI mem-broadcast struktur data sinyal baru tanpa merusak koneksi WebSocket.
- [ ] AC6: Halaman dashboard menampilkan badge Grade dan rincian trap yang terdeteksi secara responsif.
- [ ] AC7: Seluruh unit test `pytest` lulus 100%.

## Edge Cases
- **Data H4 Kosong / MT5 Offline**: Evaluasi tetap berjalan, `macro_aligned` diset False, grade dibatasi maksimal A.
- **Rentang Sesi Asia Nol**: Detektor Asian Judas di-skip (return `None`).
- **Candle Kurang untuk Warm-up RSI (< 15)**: Detektor RSI di-skip dengan aman tanpa melempar exception.
- **SL Melebihi Batas Wajar**: Dibatasi oleh cap `MAX_SL_PIPS` (15 pip) agar rasio risiko tetap terkendali.

## Out of Scope
- Eksekusi order otomatis ke akun broker (hanya signal generation).
- Backtesting visual historical replay di chart.
- Multi-pair selain XAUUSD.
