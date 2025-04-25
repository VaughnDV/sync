#!/bin/bash

# Exit on error
set -e

echo "Running database migrations..."
poetry run python src/manage.py migrate

echo "Collecting static files..."
poetry run python src/manage.py collectstatic --noinput

echo "Starting the application..."
exec "$@" 