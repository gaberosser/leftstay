# Useful Snippets

I'll assume that we are running two separate servers:
- `allentown` is running a Docker postgresql container. It has a database called `leftstay` and the username is `docker`.
- `effington` is running the web server (in Docker) and sundry Docker containers

## Setting up docker-machine

```
docker-machine create --driver arubacloud --ac_username "AWI-93709" --ac_password "<aruba_password>" --ac_endpoint "dc1" --ac_action "Attach" --ac_ip "<vps IP>" --ac_ssh_key "/home/gabriel/.ssh/id_rsa" <name_of machine>
```

Regenerate certificates

```
docker-machine regenerate-certs shirley
```

## Restarting the whole shebang

If things go wrong (and they often do), we can restart all the containers on a server as follows

```
# first, CD into the directory containing the required .yml file
gabriel@gabriel-desktop:~$ cd leftstay/
gabriel@gabriel-desktop:~/leftstay$ eval $(docker-machine env effington)
gabriel@gabriel-desktop:~/leftstay$ docker-compose -f docker-production.yml restart
Restarting leftstay_nginx_1 ... done
Restarting leftstay_flower_1 ... done
Restarting dj01 ... done
Restarting leftstay_worker_1 ... done
Restarting celery_beat ... done
Restarting leftstay_rabbit_1 ... done
```

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

## Emptying the rabbitMQ queue

Sometimes the queue can get backed up. Eventually this seems to lead to a failure. I need to find out a better way to monitor this, and ideally to fix it automatically.

Manually, we can purge the queue directly from the container. Below I assume we are using a queue named `default`.

```
gabriel@gabriel-desktop:~$ eval $(docker-machine env effington)
gabriel@gabriel-desktop:~$ docker exec -i -t 6fb86c51e7a8 bash # hash here is the rabbit container ID
root@rabbit:/# rabbitmqctl purge_queue default
Purging queue 'default' in vhost '/' ...
```