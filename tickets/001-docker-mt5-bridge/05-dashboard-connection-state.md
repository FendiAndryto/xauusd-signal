# Ticket 05: Dashboard Offline/Disconnected UI Handling

One-line goal: Sesuaikan server.py dan static/index.html agar menampilkan state disconnected tanpa data palsu saat MT5 offline.

## Scope
- Di `server.py`, tangani nilai `None` dari `get_latest_tick()` agar tidak mem-broadcast tick kosong.
- Di `static/index.html`, jika status disconnected / data candle kosong, tampilkan pesan peringatan *"MT5 Terminal Offline — Pastikan MT5 Bridge & Terminal Berjalan"*.
- Pastikan chart tidak merender candle palsu saat offline.

## Files to touch
- `server.py`
- `static/index.html`

## Verification
- Perintah: `python -c "import server; print('Server syntax OK')"`
- Hasil: `Server syntax OK`

## Depends on
- 03-mt5-feed-bridge-mode

## Status
done
