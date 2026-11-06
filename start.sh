#!/usr/bin/env bash
# Production start (Render): prepare the database, seed demo data, serve HTTP + WebSocket.
set -euo pipefail
python manage.py migrate --noinput
python manage.py seed_demo
exec daphne -b 0.0.0.0 -p "${PORT:-8000}" --proxy-headers config.asgi:application
