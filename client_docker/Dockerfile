FROM docker:20.10.14-dind-rootless
ENV TZ="Europe/Paris"

USER root
RUN apk update && apk add python3 python3-dev py3-pip gcc linux-headers musl-dev

RUN pip3 install prefect==1.2.2
