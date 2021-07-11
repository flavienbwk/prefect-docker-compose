FROM python:3.8

ARG PREFECT_CORE_VERSION

RUN apt update && apt install uuid -y
RUN pip install prefect==$PREFECT_CORE_VERSION 
