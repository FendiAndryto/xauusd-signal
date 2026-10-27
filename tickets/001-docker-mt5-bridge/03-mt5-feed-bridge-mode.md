# Ticket 03: Real-Data MT5 Feed & Bridge Client

One-line goal: Hapus seluruh kode synthetic/mock dari `core/mt5_feed.py` dan tambahkan integrasi client bridge HTTP.

## Scope
- Hapus method `_generate_mock_candles()` dan variabel `_mock_*` dari `core/mt5_feed.py`.
- Tambahkan dukungan `mode="bridge"` menggunakan library `httpx.Client` dengan timeout 2 detik.
- Jika mode direct atau bridge gagal koneksi, kembalikan list kosong `[]` untuk candle dan `None` untuk tick (tidak ada mock data).
- Update unit test untuk memastikan feed me-return data kosong saat offline.

## Files to touch
- `core/mt5_feed.py`
- `tests/test_mt5_feed.py`

## Verification
- Perintah: `pytest`
- Hasil: Semua test lulus tanpa error.

## Depends on
- 01-config-deps

## Status
done
