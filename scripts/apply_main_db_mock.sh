#!/usr/bin/env bash
# Тот же шаг, что при `docker compose up`: сервис main-db-bootstrap (DDL + CSV, идемпотентно).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
docker compose run --rm main-db-bootstrap
echo "OK: main-db-bootstrap finished"
