# A simple example to demonstrate Prefect is working as expected
# Works with a local folder shared with the agents (/root/.prefect/flows by default).

import json

import requests
from prefect import flow, task, get_run_logger
from prefect.deployments import Deployment
from prefect.filesystems import LocalFileSystem

# --- Flow definition

@task
def get_city_coordinates(city: str):
    logger = get_run_logger()
    cities = {
        "Paris": (2.3510, 48.8567)
    }
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


@flow(name="get_paris_weather")
def get_paris_weather():
    city_coordinates = get_city_coordinates("Paris")
    return get_weather(city_coordinates[0], city_coordinates[1])

# --- Deployment definition

if __name__ == '__main__':

    block_storage = LocalFileSystem(basepath="/flows")
    block_storage.save("local-storage", overwrite=True)

    deployment = Deployment.build_from_flow(
        name="get_weather_local_example",
        flow=get_paris_weather,
        storage=LocalFileSystem.load("local-storage"),
        work_queue_name="flows-example-queue"
    )
    deployment.apply()

    # --- Execute the flow

    get_paris_weather()
