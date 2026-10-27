# Ticket 01: Config Parameters and H4 Timeframe Mapping

One-line goal: Tambahkan parameter ambang batas trap di `config.py` dan mapping timeframe H4 di `core/mt5_feed.py`.

## Scope
- Di `config.py`: Tambahkan `EMA_PERIOD=200`, `ATR_PERIOD=14`, `EQL_TOLERANCE_PIPS=1.5`, `EQL_MIN_GAP_CANDLES=5`, `IFVG_MAX_AGE_CANDLES=20`, `RSI_PERIOD=14`, `RSI_OVERBOUGHT=70.0`, `RSI_OVERSOLD=30.0`, `MAX_SL_PIPS=15.0`, `ASIAN_SESSION_UTC=(0, 6)`.
- Di `core/mt5_feed.py`: Tambahkan timeframe `"H4"` pada dictionary `TF_MAP` dan `TF_SECONDS`.

## Files to touch
- `config.py`
- `core/mt5_feed.py`

## Verification
- Perintah: `python -c "from config import settings; from core.mt5_feed import TF_MAP; print(settings.EMA_PERIOD, 'H4' in TF_MAP)"`
- Hasil: `200 True`

## Depends on
None

## Status
done
