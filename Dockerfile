FROM alpine:latest AS build

# declare params
ENV ANYLOG_ROOT_DIR=/app \
    DEBIAN_FRONTEND=noninteractive \
    CONN_IP=0.0.0.0 \
    CLI_PORT=8000

WORKDIR $ANYLOG_ROOT_DIR
COPY manage.py Remote-CLI/manage.py
COPY djangoProject R


RUN mkdir -p $ANYLOG_ROOT_DIR/Remote-CLI/djangoProject/static/blobs/current/ && \
    chmod 775 $ANYLOG_ROOT_DIR && \
    apk update && apk upgrade && apk add --no-cache python3 py3-pip && apk update && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade -r $ANYLOG_ROOT_DIR/Remote-CLI/requirements.txt || true && \
    apk update


FROM build as deployment
CMD ["sh", "-c", "python3 manage.py migrate"]
ENTRYPOINT python3 /app/Remote-CLI/manage.py runserver ${CONN_IP}:${CLI_PORT}