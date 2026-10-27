# Ticket 02: Modular Trap Detectors Implementation

One-line goal: Buat modul detektor terpisah untuk 5 pola trap di direktori `core/traps/`.

## Scope
- Buat package `core/traps/` dan `core/traps/__init__.py`.
- `sweep.py`: Deteksi stop hunt sweep swing high/low dengan penolakan ekor.
- `asian_judas.py`: Deteksi sweep batas High/Low sesi Asia saat pembukaan sesi London.
- `ifvg_breaker.py`: Deteksi penembusan FVG pertama dan retest punggung zona (Inverse FVG).
- `equal_levels.py`: Deteksi Equal Highs (EQH) dan Equal Lows (EQL) dengan sweep wick.
- `rsi_divergence.py`: Deteksi secondary sweep saat terjadi RSI overbought/oversold divergence.
- Setiap fungsi detektor me-return `Optional[TrapResult]`.

## Files to touch
- `core/traps/__init__.py`
- `core/traps/sweep.py`
- `core/traps/asian_judas.py`
- `core/traps/ifvg_breaker.py`
- `core/traps/equal_levels.py`
- `core/traps/rsi_divergence.py`

## Verification
- Perintah: `python -c "import core.traps as t; print('Traps imported OK')"`
- Hasil: `Traps imported OK`

## Depends on
- 01-config-h4-mapping

## Status
done
