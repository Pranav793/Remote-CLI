FROM ubuntu:20.04

# declare params
ENV ANYLOG_ROOT_DIR=/app
ENV DEBIAN_FRONTEND=noninteractive
ENV CONN_IP=0.0.0.0
ENV CLI_PORT=31800

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install python3.9 python3-pip
RUN apt-get -y install libpq-dev python3.9-dev
RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install django
RUN python3.9 -m pip install requests
RUN apt-get -y update

WORKDIR $ANYLOG_ROOT_DIR
COPY . Remote-CLI
RUN chmod 775 $ANYLOG_ROOT_DIR

ENTRYPOINT python3.9 /app/Remote-CLI/manage.py runserver ${CONN_IP}:${CLI_PORT}
