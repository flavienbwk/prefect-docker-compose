FROM python:3.7

RUN apt update
RUN apt install uuid -y
RUN pip install prefect

WORKDIR /usr/app

ARG PREFECT_API_URL=${PREFECT_API_URL}
COPY ./weather.py /usr/app/weather.py
