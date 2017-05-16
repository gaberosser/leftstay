#!/usr/bin/env bash
# wait-for-postgres.sh
# copied and modified from Docker docs

set -e

CMD="echo '${DB_SERVICE}:${DB_PORT}:*:${POSTGRES_USER}:${POSTGRES_PASSWORD}' > ~/.pgpass && chmod 0600 ~/.pgpass"
su myuser -c "$CMD"
ls -ahl /home/myuser >&2

>&2 echo "Looking for Postgres..."

CMD="psql -h $DB_SERVICE -U $POSTGRES_USER -d $POSTGRES_DB -c '\l'"
echo $CMD >&2

until su -m myuser -c "$CMD"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"
exit 0