#!/bin/bash

prefect backend server
prefect agent start --name "$(uuid)" --api "http://192.168.254.1:4200"
