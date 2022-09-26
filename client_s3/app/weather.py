# A simple example to demonstrate Prefect is working as expected
# Works with a local folder shared with the agents (/root/.prefect/flows by default).

import io
import json
import os
import uuid
from datetime import datetime

import requests
from minio import Minio
from minio.error import S3Error
from prefect import flow, get_run_logger, task
from prefect.deployments import Deployment
from prefect.filesystems import RemoteFileSystem

# --- Flow definition


@task
def create_bucket(
    minio_endpoint,
    minio_access_key,
    minio_secret_key,
    minio_use_ssl,
    bucket_name,
):
    client = Minio(
        minio_endpoint, minio_access_key, minio_secret_key, secure=minio_use_ssl
    )
    try:
        client.make_bucket(bucket_name)
    except S3Error as ex:
        if ex.code != "BucketAlreadyOwnedByYou":
            raise ex
        print("Flows bucket already exist, skipping.", flush=True)


@task
def get_city_coordinates(city: str):
    logger = get_run_logger()
    cities = {"Paris": (2.3510, 48.8567)}
    logger.info("Getting {}'s coordinates".format(city))
    return cities[city]


@task
def get_weather(longitude: float, latitude: float):
    logger = get_run_logger()
    logger.info(f"Getting weather of latitude={latitude} and longitude={longitude}")
    api_endpoint = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m"
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        weather_data = json.loads(response.text)
        logger.debug(weather_data)
        return weather_data
    else:
        raise Exception("Failed to query " + api_endpoint)


@task
def add_text_to_bucket(
    content: str,
    minio_endpoint,
    minio_access_key,
    minio_secret_key,
    minio_use_ssl,
    bucket_name,
):
    client = Minio(
        minio_endpoint, minio_access_key, minio_secret_key, secure=minio_use_ssl
    )
    content_json = json.dumps(content)
    client.put_object(
        object_name=f"{datetime.today().strftime('%Y%m%d%H%M%S')}/weather.txt",
        bucket_name=bucket_name,
        data=io.BytesIO(str.encode(content_json)),
        length=len(content_json),
        content_type="text/plain",
    )


@flow(name="get_paris_weather_s3")
def get_paris_weather(
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_use_ssl: bool,
    artifacts_bucket_name: str,
):
    city_coordinates = get_city_coordinates("Paris")
    weather_content = get_weather(city_coordinates[0], city_coordinates[1])
    create_bucket(
        minio_endpoint,
        minio_access_key,
        minio_secret_key,
        minio_use_ssl,
        artifacts_bucket_name,
    )
    add_text_to_bucket(
        weather_content,
        minio_endpoint,
        minio_access_key,
        minio_secret_key,
        minio_use_ssl,
        artifacts_bucket_name,
    )
    return True


# --- Deployment definition

if __name__ == "__main__":
    bucket_name = os.environ.get("MINIO_PREFECT_FLOWS_BUCKET_NAME")
    artifacts_bucket_name = os.environ.get("MINIO_PREFECT_ARTIFACTS_BUCKET_NAME")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT")
    minio_use_ssl = os.environ.get("MINIO_USE_SSL") == "true"
    minio_scheme = "https" if minio_use_ssl else "http"
    minio_access_key = os.environ.get("MINIO_ACCESS_KEY")
    minio_secret_key = os.environ.get("MINIO_SECRET_KEY")

    flow_identifier = datetime.today().strftime("%Y%m%d%H%M%S-") + str(uuid.uuid4())
    block_storage = RemoteFileSystem(
        basepath=f"s3://{bucket_name}/{flow_identifier}",
        key_type="hash",
        settings=dict(
            use_ssl=minio_use_ssl,
            key=minio_access_key,
            secret=minio_secret_key,
            client_kwargs=dict(endpoint_url=f"{minio_scheme}://{minio_endpoint}"),
        ),
    )
    block_storage.save("s3-storage", overwrite=True)

    deployment = Deployment.build_from_flow(
        name="get_weather_s3_example",
        flow=get_paris_weather,
        storage=RemoteFileSystem.load("s3-storage"),
        work_queue_name="flows-example-queue",
        parameters={
            "minio_endpoint": minio_endpoint,
            "minio_access_key": minio_access_key,
            "minio_secret_key": minio_secret_key,
            "minio_use_ssl": minio_use_ssl,
            "artifacts_bucket_name": artifacts_bucket_name,
        },
    )
    deployment.apply()
