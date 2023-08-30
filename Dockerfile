FROM python:3.9-alpine

# declare params
ENV ANYLOG_ROOT_DIR=/app
ENV DEBIAN_FRONTEND=noninteractive
ENV CONN_IP=0.0.0.0 
ENV CLI_PORT=8000 

WORKDIR $ANYLOG_ROOT_DIR
COPY . Remote-CLI
RUN mkdir -p $ANYLOG_ROOT_DIR/Remote-CLI/djangoProject/static/blobs/current/
RUN chmod 775 $ANYLOG_ROOT_DIR

RUN apk update 
RUN apk upgrade
RUN apk add bash-completion
RUN apk update

RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install --upgrade -r $ANYLOG_ROOT_DIR/Remote-CLI/requirements.txt || true
RUN apk update

RUN python3.9 /app/Remote-CLI/manage.py migrate
ENTRYPOINT python3.9 /app/Remote-CLI/manage.py runserver ${CONN_IP}:${CLI_PORT}
