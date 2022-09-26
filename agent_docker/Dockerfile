FROM docker:20.10-dind-rootless
ENV TZ="Europe/Paris"

USER root
RUN apk update && apk add build-base libffi-dev python3 python3-dev py3-pip gcc linux-headers musl-dev util-linux

RUN pip3 install --upgrade pip && pip3 install prefect==2.4.2
