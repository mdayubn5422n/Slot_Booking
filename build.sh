#!/usr/bin/env bash
# Build script used by hosting services such as Render (see README).
set -o errexit
pip install -r requirements-prod.txt
python manage.py collectstatic --no-input
python manage.py migrate
