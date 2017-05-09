#!/bin/sh

# wait for PSQL server to start
sleep 4

# migrate db, so we have the latest db schema
python manage.py migrate

# collect static files
python manage.py collectstatic --noinput

# run gunicorn
su -m myuser -c "gunicorn leftstay.wsgi:application -w 2 -b :8000"
