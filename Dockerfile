FROM python:3.11-alpine as base

# declare params
ENV ROOT_DIR=/app \
    DEBIAN_FRONTEND=noninteractive \
    CONN_IP=0.0.0.0 \
    CLI_PORT=8000

WORKDIR $ROOT_DIR
COPY djangoProject $ROOT_DIR/Remote-CLI/djangoProject
COPY manage.py $ROOT_DIR/Remote-CLI/manage.py
COPY requirements.txt $ROOT_DIR/Remote-CLI/requirements.txt

WORKDIR $ROOT_DIR/Remote-CLI
RUN mkdir -p $ROOT_DIR/Remote-CLI/djangoProject/static/blobs/current/ && \
    chmod 775 $ROOT_DIR && \
    apk update && apk upgrade && \
    apk update && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade -r $ROOT_DIR/Remote-CLI/requirements.txt || true && \
    apk del py3-pip && \
    apk update && \
    rm -rf $ROOT_DIR/Remote-CLI/requirements.txt $ROOT_DIR/Remote-CLI/json/commands_orig.json $ROOT_DIR/Remote-CLI/json/nvidia.json \
           $ROOT_DIR/Remote-CLI/json/nvidia.json

# Stage 2: Deployment
FROM base as deployment
WORKDIR /app/Remote-CLI

# Perform migrations and run the server in the background and redirect output
CMD ["sh", "-c", "python3 manage.py migrate"]
ENTRYPOINT python3 manage.py runserver ${CONN_IP}:${CLI_PORT}
