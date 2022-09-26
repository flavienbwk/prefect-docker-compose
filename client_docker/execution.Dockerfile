FROM python:3.10

RUN apt update && apt install uuid -y
RUN pip install prefect==2.3.2
