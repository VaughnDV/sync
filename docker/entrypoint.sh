#!/bin/bash


if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "MAKING MIGRATIONS"
python manage.py migrate
echo "COLLECTING STATIC FILES"
python manage.py collectstatic --no-input --clear
echo "Entry point script finished"
exec "$@" 