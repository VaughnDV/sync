#!/bin/bash

# Exit on error
set -e

wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! pg_isready -h db -U postgres -p 5432 > /dev/null 2>&1; do
        echo "Database is not ready yet. Waiting..."
        sleep 2
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