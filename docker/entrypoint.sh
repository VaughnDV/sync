#!/bin/bash

set -e

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Making migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Entry point script finished"

exec "$@"
