# Ticket 02: MT5 Windows Host Bridge Implementation

One-line goal: Buat server bridge mandiri di host Windows untuk mengekspos data real-time MT5 via HTTP.

## Scope
- Buat `mt5_bridge.py` menggunakan FastAPI yang berjalan di port `8081`.
- Endpoint `GET /status`: Mengembalikan status inisialisasi MT5 dan simbol.
- Endpoint `GET /tick`: Mengembalikan tick bid/ask/last real langsung dari `mt5.symbol_info_tick()`. Return HTTP 503 jika MT5 offline/gagal.
- Endpoint `GET /candles`: Mengembalikan candle real langsung dari `mt5.copy_rates_from_pos()`. Return HTTP 503 jika MT5 offline/gagal.
- Tanpa mock data atau data buatan sama sekali.

## Files to touch
- `mt5_bridge.py`

## Verification
- Perintah: `python -c "import mt5_bridge; print('Bridge syntax OK')"`
- Hasil: `Bridge syntax OK`

## Depends on
- 01-config-deps

## Status
done
