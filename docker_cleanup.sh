#!/bin/bash

# remove all exited containers
docker rm $(docker ps -a -f status=exited -q)

# remove all dangling images
docker rmi $(docker images -f dangling=true -q)

# remove all dangling volumes
# NB: this will delete the postgresql database if the container is not running!!
# docker volume rm $(docker volume ls -f dangling=true -q)
