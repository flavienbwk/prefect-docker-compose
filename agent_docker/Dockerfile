FROM docker:19.03.13-dind-rootless

ARG PREFECT_CORE_VERSION

USER root
RUN apk update && apk add python3 python3-dev py3-pip gcc linux-headers musl-dev util-linux
RUN pip3 install prefect==$PREFECT_CORE_VERSION 