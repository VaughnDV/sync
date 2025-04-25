#!/bin/bash
if [ "$DATABASE_URL" != "" ]
then
    echo "Waiting for postgres..."

    # Extract host and port from DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | cut -d'@' -f2 | cut -d':' -f1)
    DB_PORT=$(echo $DATABASE_URL | cut -d':' -f4 | cut -d'/' -f1)

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Exit on error
set -e

echo "Running database migrations..."
python src/manage.py migrate

echo "Collecting static files..."
python src/manage.py collectstatic --noinput

echo "Starting the application..."
exec "$@" 