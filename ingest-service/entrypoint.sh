#!/bin/bash

# Wait for dependencies
echo "Waiting for dependencies..."
python /app/scripts/wait_for_dependencies.py

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting ingest service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 