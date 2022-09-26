#!/bin/sh
docker login -u=${REGISTRY_USERNAME} -p=${REGISTRY_PASSWORD} "${REGISTRY_SCHEME}://${REGISTRY_ENDPOINT}"
python3 /usr/app/weather.py
