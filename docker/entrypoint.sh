#!/bin/bash

# Exit on error
set -e

# Install postgresql-client for pg_isready
if ! command -v pg_isready &> /dev/null; then
    echo "Installing postgresql-client..."
    apt-get update && apt-get install -y postgresql-client
fi

wait_for_db() {
    echo "Waiting for database to be ready..."
    max_attempts=30
    attempt=1
    while ! pg_isready -h db -U postgres -p 5432 > /dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo "Database connection failed after $max_attempts attempts"
            exit 1
        fi
        echo "Database is not ready yet. Waiting... (Attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "Database is ready!"
}

# Wait for the database to be ready
wait_for_db

echo "Running database migrations..."
poetry run python src/manage.py migrate

echo "Collecting static files..."
poetry run python src/manage.py collectstatic --noinput

echo "Starting the application..."
exec "$@" 