FROM docker:19.03.13-dind-rootless

USER root
RUN apk update
RUN apk add python3 python3-dev py3-pip gcc linux-headers musl-dev

RUN pip3 install prefect
ENV TZ="Europe/Paris"

COPY ./exec_env.Dockerfile /root/Dockerfile
