FROM python:3.10

RUN apt update && apt install uuid -y
RUN pip3 install --upgrade pip && pip3 install prefect==2.4.2
