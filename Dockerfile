FROM python:3.11-alpine as base

# declare params
ENV ROOT_DIR=/app \
    DEBIAN_FRONTEND=noninteractive \
    CONN_IP=0.0.0.0 \
    CLI_PORT=8000

WORKDIR $ROOT_DIR
COPY djangoProject $ROOT_DIR/Remote-CLI/djangoProject
COPY setup.py $ROOT_DIR/Remote-CLI/setup.py
COPY manage_old.py $ROOT_DIR/Remote-CLI/manage.py
COPY setup.cfg $ROOT_DIR/Remote-CLI/setup.cfg
COPY requirements.txt $ROOT_DIR/Remote-CLI/requirements.txt

WORKDIR $ROOT_DIR/Remote-CLI

RUN mkdir -p $ROOT_DIR/Remote-CLI/djangoProject/static/blobs/current/ && \
    chmod 775 $ROOT_DIR && \
    apk update && apk upgrade && \
    apk update && \
    apk add bash build-base && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade -r $ROOT_DIR/Remote-CLI/requirements.txt || true && \
    python3 $ROOT_DIR/Remote-CLI/setup.py bdist_wheel && \
    python3 -m pip install --upgrade  dist/anylog_remote_cli-1.0.0*.whl && \
    apk update

COPY djangoProject/static/* /usr/local/lib/python3.11/site-packages/djangoProject/static

RUN rm -rf  $ROOT_DIR/Remote-CLI/djangoProject/*.py $ROOT_DIR/Remote-CLI/djangoProject/*.c $ROOT_DIR/Remote-CLI/djangoProject/*.o  \
            $ROOT_DIR/Remote-CLI/djangoProject/anylog_conn $ROOT_DIR/Remote-CLI/djangoProject/migrations $ROOT_DIR/Remote-CLI/djangoProject/templates \
            $ROOT_DIR/Remote-CLI/djangoProject/static/css $ROOT_DIR/Remote-CLI/requirements.txt $ROOT_DIR/Remote-CLI/json/commands_orig.json  \
            $ROOT_DIR/Remote-CLI/json/nvidia.json $ROOT_DIR/Remote-CLI/json/nvidia.json

# Stage 2: Deployment
FROM base as deployment

ENTRYPOINT /bin/bash

# Perform migrations and run the server in the background and redirect output
#CMD ["sh", "-c", "python3 $ROOT_DIR/Remote-CLI/manage.py migrate"]
#ENTRYPOINT python3 $ROOT_DIR/Remote-CLI/manage.py runserver ${CONN_IP}:${CLI_PORT}
