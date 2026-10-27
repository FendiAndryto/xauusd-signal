# Ticket 04: SMC Engine Orchestrator and Comprehensive Tests

One-line goal: Refactor `core/smc_engine.py` untuk mengorkestrasi seluruh detektor trap, menghitung level SL/TP gabungan, dan membuat unit test pytest lengkap.

## Scope
- Update `Signal` dan buat dataclass `TrapResult` di `core/smc_engine.py`.
- Refactor method `evaluate(candles, h4_candles)`:
  - Jalankan 5 detektor trap.
  - Cek directional guard: jika ada perbedaan arah (Buy vs Sell), kembalikan `None`.
  - Hitung SL dari titik ekstrem terjauh dari trap yang terpicu + buffer pip.
  - Tentukan TP dengan rasio minimum RR 1:2.0.
  - Hitung Grade dan Macro alignment via `confluence.py`.
- Buat file pengujian `tests/test_traps.py` yang menguji:
  - Masing-masing dari kelima trap secara terisolasi.
  - Konflik arah sinyal menghasilkan `None`.
  - Skenario Grade B, Grade A, dan Grade A+.

## Files to touch
- `core/smc_engine.py`
- `tests/test_traps.py`
- `tests/test_smc_engine.py`

## Verification
- Perintah: `pytest`
- Hasil: Semua test di `test_traps.py` dan test existing lulus 100%.

## Depends on
- 02-trap-detectors
- 03-confluence-scorer

## Status
done
