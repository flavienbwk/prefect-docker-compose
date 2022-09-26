FROM python:3.10

RUN apt update && apt install uuid -y
RUN pip install prefect==2.4.2 psycopg2-binary==2.9.3 s3fs==2022.8.2 minio==7.1.11

WORKDIR /usr/app
