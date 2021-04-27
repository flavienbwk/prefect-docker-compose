# Python version must be > 3.7 because docker:19.03.13-dind-rootless, 
# used by our agent_docker is running on version 3.8.8.
FROM python:3.8

RUN apt update && apt install uuid -y
RUN pip install prefect
