FROM ubuntu:20.04

RUN apt-get update

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get install -y \
    python3.8 \
    python3-pip \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libpq-dev \
    && pip3 install pipenv 

ENV PYTHONIOENCODING=utf-8
ENV LANG en_US.UTF-8
ENV LC_ALL="en_US.UTF-8"
ENV LC_CTYPE="en_US.UTF-8"

COPY Pipfile* ./

RUN pipenv install --verbose

COPY init_model.py ./

RUN pipenv run python init_model.py

COPY ./app /app
