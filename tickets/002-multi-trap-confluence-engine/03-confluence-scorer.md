# Ticket 03: Confluence Scorer and Macro Trend Filter

One-line goal: Buat modul scoring konfluensi (Grade B, A, A+) dan validasi trend macro H4 EMA 200 / ATR.

## Scope
- Buat `core/confluence.py`.
- Implementasikan fungsi `evaluate_macro_trend(h4_candles, ema_period, atr_period)` untuk menentukan bias trend (BULLISH, BEARISH, NEUTRAL).
- Implementasikan fungsi `score_confluence(traps, h4_candles)`:
  - 1 trap -> Grade "B"
  - 2 traps -> Grade "A"
  - 3+ traps -> Grade "A+" jika selaras dengan macro H4; Grade "A" jika tidak selaras.
  - Return `(grade, macro_aligned, score_count)`.

## Files to touch
- `core/confluence.py`

## Verification
- Perintah: `python -c "import core.confluence; print('Confluence module OK')"`
- Hasil: `Confluence module OK`

## Depends on
- 01-config-h4-mapping
- 02-trap-detectors

## Status
done
