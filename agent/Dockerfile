FROM python:3.7

RUN apt update
RUN apt install uuid -y
RUN pip install prefect

COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "bash", "entrypoint.sh" ]