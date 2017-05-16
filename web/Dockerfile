FROM python:2.7

RUN apt-get update && apt-get install -y \
    binutils \
    gdal-bin \
    libproj-dev \
    postgresql-client

ADD REQUIREMENTS.txt /usr/src/app/REQUIREMENTS.txt
WORKDIR /usr/src/app/
RUN pip install -r REQUIREMENTS.txt

# create unprivileged user
RUN adduser --disabled-password --gecos '' myuser

# create the local outputs directory
RUN mkdir /usr/src/app/local_outputs
