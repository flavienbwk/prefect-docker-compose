# A simple example to demonstrate Prefect is working as expected
# Works with a local folder shared with the agents (/root/.prefect/flows by default).

import json
import requests
import prefect
from prefect import Flow, task, Client
from prefect.environments.storage import Docker

logger = prefect.context.get("logger")


@task
def get_woeid(city: str):
    logger.info("Getting {}'s woeid".format(city))
    api_endpoint = "https://www.metaweather.com/api/location/search/?query={}".format(
        city
    )
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        payload = json.loads(response.text)
        return payload[0]["woeid"]
    else:
        raise Exception("Failed to query " + api_endpoint)


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
        raise Exception("Failed to query " + api_endpoint)


with Flow(
    "Get Paris' weather",
    storage=Docker(
        base_url="unix:///var/run/docker.sock",
        registry_url="172.17.0.1:5000",
        base_image="172.17.0.1:5000/weather/base_image:latest",
        ignore_healthchecks=True
    ),
) as flow:
    woeid = get_woeid("Paris")
    weather_data = get_weather(woeid)

if __name__ == "__main__":
    try:
        client = Client()
        client.create_project(project_name="weather")
    except prefect.utilities.exceptions.ClientError as e:
        logger.info("Project already exists")

    flow.register(project_name="weather", labels=["development"], add_default_labels=False)

    # Optionally run the code now
    flow.run()
