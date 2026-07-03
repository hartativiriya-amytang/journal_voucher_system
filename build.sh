#!/usr/bin/env bash

set -o errexit

pip install -r apps/requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

gunicorn --config gunicorn.conf.py
