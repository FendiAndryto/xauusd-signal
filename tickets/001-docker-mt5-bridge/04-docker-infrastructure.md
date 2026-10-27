# Ticket 04: Docker Infrastructure Setup

One-line goal: Buat file Dockerfile, docker-compose.yml, dan .dockerignore untuk menjalankan dashboard container.

## Scope
- Buat `Dockerfile` berbasis `python:3.14-slim`, meng-install `requirements-docker.txt`, dan menjalankan uvicorn pada port 8000.
- Buat `docker-compose.yml` dengan konfigurasi service `dashboard`, port mapping 8000:8000, environment `MT5_MODE=bridge`, dan `extra_hosts` untuk resolusi `host.docker.internal`.
- Buat `.dockerignore` untuk mengecualikan `.git`, `__pycache__`, docs, tests, tickets, dan bridge script.

## Files to touch
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

## Verification
- Perintah: `docker compose config`
- Hasil: Menghasilkan konfigurasi docker compose yang valid tanpa sintaks error.

## Depends on
- 01-config-deps

## Status
done
