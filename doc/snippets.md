# Useful Snippets

I'll assume that we are running two separate servers:
- `allentown` is running a Docker postgresql container. It has a database called `leftstay` and the username is `docker`.
- `effington` is running the web server (in Docker) and sundry Docker containers

## Accessing the postgresql database using `psql`

The postgresql client `psql` is not (necessarily) installed on the server running the postgresql container. Even if it were, the container is not exposed to the general system. So we cannot just SSH into the server and run `psql`.

Instead, we need to execute psql on the docker container itself.

```
# this sets the environment variables so that docker commands are run on the allentown server
gabriel@gabriel-desktop:~$ eval $(docker-machine env allentown)
gabriel@gabriel-desktop:~$ docker ps
CONTAINER ID        IMAGE                        COMMAND                  CREATED             STATUS              PORTS                    NAMES
af9ca16483e1        mdillon/postgis:9.6-alpine   "docker-entrypoint.s…"   9 months ago        Up 9 months         0.0.0.0:5432->5432/tcp   pg01
gabriel@gabriel-desktop:~$ docker exec -i -t pg01 /bin/bash
bash-4.3# psql -U docker leftstay
psql (9.6.3)
Type "help" for help.

leftstay=# 
```

And we're in!