#!/bin/sh

# wait for RabbitMQ server to start
sleep 4



# run Celery worker with Celery configuration stored in celeryconf
# we're disabling concurrency for this worker because it will be used to make HTTP requests
su -m myuser -c "celery worker -A celerystick.conf -Q default -n default@%h -l INFO --concurrency=1"
