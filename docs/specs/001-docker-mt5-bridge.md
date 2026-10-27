# SPEC-001: Docker Containerization with Host MT5 Bridge (Strictly Real Data)

## Goal
Menjalankan aplikasi dashboard dan sinyal XAUUSD di dalam container Docker (Linux), dengan menghubungkan data market real-time langsung dari MetaTrader 5 (Windows Host) melalui bridge service lokal. Menghapus seluruh mekanisme synthetic/mock data.

## Requirements
1. **Strictly Real Data**: Seluruh data candle, tick, dan sinyal wajib berasal dari MetaTrader 5 terminal aktif. Dilarang menggunakan mock/synthetic fallback.
2. **MT5 Host Bridge**: Service ringan (`mt5_bridge.py`) di Windows host berjalan di port `8081` untuk mengambil data dari MT5 IPC dan mengeksposnya via REST API.
3. **Containerized Dashboard**: Service utama (`server.py`, `core/`, `static/`) berjalan di dalam Docker container via `docker-compose.yml`.
4. **Bridge Integration**: `core/mt5_feed.py` mendukung mode `bridge` yang membaca data dari `http://host.docker.internal:8081`. Jika MT5 offline, kembalikan data kosong dan tandai status disconnected.
5. **Direct Mode Backward Compatibility**: Mode direct (menjalankan aplikasi langsung di Windows host tanpa Docker) tetap didukung via konfigurasi `MT5_MODE=direct`.

## Impact Analysis (Files Touched)
- `config.py`: Penambahan parameter `MT5_MODE` ("direct" | "bridge") dan `MT5_BRIDGE_URL`.
- `mt5_bridge.py` *(Baru)*: Server FastAPI mandiri untuk host Windows (port 8081) membaca data C-API MT5.
- `core/mt5_feed.py`: Penghapusan seluruh mock generator; penambahan HTTP client untuk bridge mode.
- `requirements.txt`: Penambahan package `httpx`.
- `requirements-docker.txt` *(Baru)*: Dependency Docker tanpa package Windows-only `MetaTrader5`.
- `Dockerfile` *(Baru)*: Build image container Linux berbasis Python.
- `docker-compose.yml` *(Baru)*: Konfigurasi service dashboard, port mapping, dan host gateway.
- `.dockerignore` *(Baru)*: Filter file cache, docs, tickets, dan bridge script.
- `server.py`: Update penanganan status disconnect saat MT5 belum mengirim tick real.
- `static/index.html`: Update visual UI untuk menampilkan status disconnected saat tidak ada data real.

## Acceptance Criteria
- [ ] AC1: `mt5_bridge.py` berjalan di host Windows dan merespons `GET /status`, `GET /tick`, dan `GET /candles`.
- [ ] AC2: Seluruh logika mock di `core/mt5_feed.py` dihapus; fungsi me-return `None` atau list kosong saat disconnected.
- [ ] AC3: `Dockerfile` dan `docker-compose.yml` berhasil di-build tanpa error package Windows.
- [ ] AC4: Dashboard di dalam container (`http://localhost:8000`) menerima data real saat bridge aktif.
- [ ] AC5: Dashboard menampilkan status 'MT5 Disconnected' saat terminal/bridge tidak aktif (tidak ada candle palsu).
- [ ] AC6: Seluruh unit test `pytest` lulus tanpa regresi.

## Edge Cases
- **MT5 Terminal Ditutup**: Bridge mengembalikan HTTP 503 / `connected: false`. Container tidak crash dan UI menampilkan status disconnected.
- **Bridge Network Timeout**: Request HTTP dibatasi timeout 2.0 detik agar event loop tidak menggantung.
- **Linux Docker Host Gateway**: `docker-compose.yml` menggunakan `extra_hosts: host.docker.internal:host-gateway` agar resolusi host berfungsi lintas platform.

## Out of Scope
- Eksekusi order / automated trading ke MT5 (hanya data market read-only).
- Penggunaan Wine di dalam Docker container.
- Autentikasi / enkripsi TLS antar container dan host (keduanya berjalan di mesin lokal).
