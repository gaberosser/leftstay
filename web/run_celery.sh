#!/bin/sh

# wait for RabbitMQ server to start
sleep 4

# run Celery worker with Celery configuration stored in celeryconf
su -m myuser -c "celery worker -A celerystick.conf -Q default -n default@%h -l INFO"

# run flower here?
