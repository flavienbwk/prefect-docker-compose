#!/bin/bash

prefect backend server
prefect agent start --name "$(uuid)" --api ${PREFECT_SERVER__APOLLO_URL}
