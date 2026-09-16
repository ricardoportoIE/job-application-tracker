#!/bin/sh
set -eu

/app/.venv/bin/python -m app.db.migrations

unset DB_ADMIN_USER
unset DB_ADMIN_PASSWORD

exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
