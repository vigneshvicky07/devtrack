#!/bin/sh
set -e

echo "=== Running Django Database Migrations ==="
python manage.py makemigrations --noinput
python manage.py migrate --noinput
echo "=== Migrations Complete ==="

echo "=== Starting DevTrack Server on 0.0.0.0:8000 ==="
exec python manage.py runserver 0.0.0.0:8000
