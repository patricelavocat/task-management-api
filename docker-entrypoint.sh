#!/bin/sh
set -e

echo "Running database migrations..."
alembic -c alembic.ini -x alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
