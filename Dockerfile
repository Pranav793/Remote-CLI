FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get -y update

# install requirements via apt
RUN apt-get -y install python3.8 python3-pip
RUN apt-get -y install libpq-dev python3.8-dev

RUN python3.8 -m pip install --user Django || true
RUN python3.8 -m pip install requests || true
RUN python3.8 -m pip install docker || true

WORKDIR /app
COPY . Django-API
RUN chmod 775 /app
EXPOSE 8000

ENTRYPOINT python3.8 /app/Django-API/manage.py runserver ${LOCAL_CONN}
