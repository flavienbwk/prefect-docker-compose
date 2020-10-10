# A simple example to demonstrate Prefect is working as expected
# Works with a local folder shared with the agents (/root/.prefect/flows by default).

import os
import json
import time
import uuid
import requests
import datetime
import s3_utils

import prefect
from prefect import Flow, task, Client, config
from prefect.environments import LocalEnvironment
from prefect.environments.storage import Webhook

logger = prefect.context.get("logger")

@task
def get_woeid(city: str):
    logger.info("Getting {}'s woeid".format(city))
    api_endpoint = "https://www.metaweather.com/api/location/search/?query={}".format(city)
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        payload = json.loads(response.text)
        return payload[0]["woeid"]
    else:
        raise("Failed to query " + api_endpoint)

@task
def get_weather(woeid: int):
    logger.info("Getting weather of {}".format(woeid))
    api_endpoint = "https://www.metaweather.com/api/location/{}".format(woeid)
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        weather_data = json.loads(response.text)
        logger.debug(weather_data)
        return weather_data
    else:
        raise("Failed to query " + api_endpoint)

# Webhook for Minio S3 upload and download
s3_bucket = "prefect" # previously created (in README.md)
s3_flow_filename = uuid.uuid4()
s3_headers_upload = s3_utils.get_headers(
    method="PUT",
    key=config.s3.key,
    secret=config.s3.secret,
    host=config.s3.endpoint,
    bucket=s3_bucket,
    file_name=s3_flow_filename
)
s3_headers_download = s3_utils.get_headers(
    method="GET",
    key=config.s3.key,
    secret=config.s3.secret,
    host=config.s3.endpoint,
    bucket=s3_bucket,
    file_name=s3_flow_filename
)
with Flow(
        "Get Paris' weather",
        storage=Webhook(
            build_request_kwargs={
                "url": "http://{}/{}/{}".format(config.s3.endpoint, s3_bucket, s3_flow_filename),
                "headers": s3_headers_upload
            },
            build_request_http_method="PUT",
            get_flow_request_kwargs={
                "url": "http://{}/{}/{}".format(config.s3.endpoint, s3_bucket, s3_flow_filename),
                "headers": s3_headers_download
            },
            get_flow_request_http_method="GET",
        )
    ) as flow:
    woeid = get_woeid("Paris")
    weather_data = get_weather(woeid)

try:
    client = Client()
    client.create_project(project_name="weather")
except prefect.utilities.exceptions.ClientError as e:
    logger.info("Project already exists")

flow.storage.build()
flow.register(project_name="weather", labels=["development"])

# Optionally run the code now
flow.run()
