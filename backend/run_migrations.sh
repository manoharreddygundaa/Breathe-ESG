#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

echo "Seeding demo data..."
python manage.py seed_demo

echo "Database ready!"
