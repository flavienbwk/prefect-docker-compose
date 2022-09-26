# A simple example to demonstrate Prefect is working as expected
# Works with a local folder shared with the agents (/root/.prefect/flows by default).

import json
import os
import shutil
import tarfile
import tempfile
import uuid
from datetime import datetime

import requests
from prefect import flow, get_run_logger, task
from prefect.deployments import Deployment
from prefect.infrastructure.docker import DockerContainer, DockerRegistry

# --- Flow definition


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


@flow(name="get_paris_weather_docker")
def get_paris_weather():
    city_coordinates = get_city_coordinates("Paris")
    weather_content = get_weather(city_coordinates[0], city_coordinates[1])
    logger = get_run_logger()
    logger.info(weather_content)
    return True


# --- Deployment definition

if __name__ == "__main__":
    from io import BytesIO
    from docker import APIClient

    flow_identifier = datetime.today().strftime("%Y%m%d%H%M%S-") + str(uuid.uuid4())

    # Mimicking Prefect 1.x image build for Prefect 2.x

    ## 1. Creating Docker build context (including flow files)
    base_image = f"{os.environ.get('REGISTRY_ENDPOINT')}/weather/base_image:latest"
    flow_image = (
        f"{os.environ.get('REGISTRY_ENDPOINT')}/weather/flow_image:{flow_identifier}"
    )
    dockerfile = f"""
    FROM {base_image}
    RUN mkdir -p /usr/app
    COPY ./flow /usr/app
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        ### a. Creating archive with context (flow files + Dockerfile) for Docker build API
        os.makedirs(f"{tmp_path}/build")
        with open(f"{tmp_path}/build/Dockerfile", "w+") as the_file:
            the_file.write(dockerfile)
        shutil.copytree("/usr/app", f"{tmp_path}/build/flow")
        with tarfile.open(f"{tmp_path}/flow.tar", "w") as tar:
            tar.add(f"{tmp_path}/build", arcname=".")
        ### b. Build image with context
        with open(f"{tmp_path}/flow.tar", "rb") as fh:
            docker_build_archive = BytesIO(fh.read())
        cli = APIClient(base_url="unix:///var/run/docker.sock")
        for line in cli.build(
            fileobj=docker_build_archive, custom_context=True, rm=True, tag=flow_image
        ):
            print(line, flush=True)
        for line in cli.push(flow_image, stream=True, decode=True):
            print(line, flush=True)

    ## 2. Registering flow
    dockerhub = DockerRegistry(
        username=os.environ.get("REGISTRY_USERNAME"),
        password=os.environ.get("REGISTRY_PASSWORD"),
        reauth=True,
        registry_url=f"{os.environ.get('REGISTRY_SCHEME')}://{os.environ.get('REGISTRY_ENDPOINT')}",
    )
    dockerhub.save("docker-storage", overwrite=True)
    docker_block = DockerContainer(
        image=flow_image,
        image_registry=dockerhub,
    )
    docker_block.save("docker-storage", overwrite=True)

    deployment = Deployment.build_from_flow(
        name="get_weather_docker_example",
        flow=get_paris_weather,
        infrastructure=docker_block,  # storage block is automatically detected from https://github.com/PrefectHQ/prefect/pull/6574/files
        work_queue_name="flows-example-queue-docker",
        path="/usr/app",
    )
    deployment.apply()
