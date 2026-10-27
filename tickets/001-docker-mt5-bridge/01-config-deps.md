# Ticket 01: Configuration and Dependencies Update

One-line goal: Tambahkan konfigurasi bridge dan pisahkan dependency Docker tanpa package Windows-only.

## Scope
- Tambahkan `MT5_MODE` (default "direct") dan `MT5_BRIDGE_URL` (default "http://host.docker.internal:8081") di `config.py`.
- Tambahkan `httpx` di `requirements.txt`.
- Buat file `requirements-docker.txt` berisi dependency Linux container (tanpa `MetaTrader5`).

## Files to touch
- `config.py`
- `requirements.txt`
- `requirements-docker.txt`

## Verification
- Perintah: `python -c "from config import settings; print(settings.MT5_MODE, settings.MT5_BRIDGE_URL)"`
- Hasil: `direct http://host.docker.internal:8081`

## Depends on
None

## Status
done
