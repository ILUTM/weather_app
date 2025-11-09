#!/bin/sh

set -e 

echo "Database is ready, applying migrations..."
poetry run python manage.py migrate --noinput

echo "Loading city data..."
poetry run python manage.py cities_light

echo "Starting server..."
exec poetry run python manage.py runserver 0.0.0.0:8000
