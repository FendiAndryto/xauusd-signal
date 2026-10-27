# Ticket 05: Server Integration and Dashboard UI Visuals

One-line goal: Sambungkan engine baru ke background poller server.py dan perbarui tampilan web dashboard untuk menampilkan Grade badge dan Trap tags.

## Scope
- Di `server.py`:
  - Ambil candle H4 secara berkala untuk filter macro.
  - Kirim field baru (`grade`, `traps`, `macro_aligned`, `confluence_score`) pada payload WebSocket dan status API.
- Di `static/index.html`:
  - Tambahkan style CSS untuk badge Grade: `B` (kuning), `A` (biru), `A+` (hijau bersinar / glow).
  - Tampilkan list pill tag untuk setiap nama trap yang berkontribusi pada sinyal.
  - Tampilkan ikon checklist / indikator jika macro H4 selaras.

## Files to touch
- `server.py`
- `static/index.html`

## Verification
- Perintah: `python -c "import server; print('Server syntax OK')"`
- Hasil: `Server syntax OK`

## Depends on
- 04-smc-engine-orchestrator

## Status
done
