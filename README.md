# Prefect - Docker Compose

A simple guide to understand and make Prefect work with your own docker-compose configuration.

This allows you to package your Prefect instance for Kubernetes or offline use.

![Operating principle of Prefect](./prefect_schema_principle.jpg)

- [Prefect - Docker Compose](#prefect---docker-compose)
  - [Run the server](#run-the-server)
  - [Run one or multiple agents](#run-one-or-multiple-agents)
  - [Run your first flow via the Prefect API](#run-your-first-flow-via-the-prefect-api)
    - [Principles to understand](#principles-to-understand)
    - [Flow with Local storage (easiest)](#flow-with-local-storage-easiest)
    - [Flow with S3 Storage](#flow-with-s3-storage)
    - [Flow with Docker storage](#flow-with-docker-storage)
      - [Start the Docker in Docker agents](#start-the-docker-in-docker-agents)
      - [Preparing the Registry](#preparing-the-registry)
      - [Registering the flow](#registering-the-flow)

## Run the server

Open and edit the [`server/.env`](./server/.env) file.  
All `PREFECT_SERVER_*` options are [explained in the official documentation](https://docs.prefect.io/core/concepts/configuration.html#environment-variables) and [listed in the `config.toml` file](https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml).

Then you can run :

```bash
docker-compose -f server/docker-compose.yml up -d
```

Insert the following content in file `~/.prefect/config.toml` :

```conf
# ~/.prefect/config.toml
debug = true

# base configuration directory (typically you won't change this!)
home_dir = "~/.prefect"

backend = "server"

[server]
host = "http://172.17.0.1"
port = "4200"
host_port = "4200"
endpoint = "${server.host}:${server.port}"
```

Finally, we need to create a _tenant_. Execute on your host :

```bash
pip3 install prefect
prefect backend server
prefect server create-tenant --name default --slug default
```

Access the UI at [localhost:8080](http://localhost:8080)

## Run one or multiple agents

Agents are services that run your scheduled flows.

Open and edit the [`agent/config.toml`](./agent/config.toml) file.

> :information_source: In each `config.toml`, you will find the `172.17.0.1` IP address. This is the IP of the Docker daemon on which are exposed all exposed ports of your containers. This allows containers launched from different docker-compose networks to communicate. Change it if yours is different (check your daemon IP by typing `ip a | grep docker0`).
> 
> ![Docker interface IP](./docker_interface.png)
> 
> Here, mine is `192.168.254.1` but the default is generally to `172.17.0.1`.

Then you can run :

```bash
docker-compose -f agent/docker-compose.yml up -d
```

> :information_source: You can run the agent on another machine than the one with the Prefect server. Edit the [`agent/config.toml`](./agent/config.toml) file for that.

Maybe you want to instanciate multiple agents automatically ?

```bash
docker-compose -f agent/docker-compose.yml up -d --scale agent=3 agent
```

## Run your first flow via the Prefect API

### Principles to understand

> :speech_balloon: [Execution in your cloud; orchestration in ours](https://medium.com/the-prefect-blog/the-prefect-hybrid-model-1b70c7fd296)

This means the Prefect server never stores your code. It just orchestrates the running (optionally the scheduling) of it.

1. When coding a flow, you need first to [**register it** to the Prefect server](./client/weather.py#L50) through a script. In that script, you may ask the server to run your flow 3 times a day, for example.
2. Your code never lies on the Prefect server : this means the code has to be stored somewhere accessible to the agents in order to be executed.

    Prefect has [a lot of storage options](https://docs.prefect.io/orchestration/execution/storage_options.html) but the most famous are : Local, S3 and Docker.

    - Local : saves the flows to be run on disk. So the volume where you save the flows must be [shared among your client and your agent(s)](./client/docker-compose.yml#L9). Requires your agent to have the same environment than your client (Python modules, packages installed etc... (the same Dockerfile if your agent and client are containers))
    - S3 : similar to local, but saves the flows to be run in S3 objects.
    - Docker : saves the flows to be run as Docker images to your Docker Registry so your agents can easily run the code.

### Flow with Local storage (easiest)

:information_source: If your agents are installed among multiple machines, I recommend you to mount a shared directory with SSHFS.

Open the [`client/config.toml`](./client/config.toml) file and edit the IP to match your Prefect instance. Then you can run :

```bash
docker-compose -f client/docker-compose.yml up # Executes weather.py
```

Now your flow is registered. You can access the UI to run it.

### Flow with S3 Storage

:warning: I don't recommend this method if you plan to schedule a lot of flows every minute. MinIO times out regurarly in that case (maybe AWS wouldn't).

<details>
<summary>Tutorial for S3 Storage</summary>
<br/>

We will use [MinIO](https://www.github.com/minio/minio) as our S3 server.

```bash
docker-compose -f client_s3/docker-compose.yml up -d minio # Starts MinIO
```

1. Go to [localhost:9000](http://localhost:9000) create a new **bucket** named `prefect` by clicking the red **(+)** button bottom right.

2. Open the [`client/config.toml`](./client/config.toml) file and edit the IP to match your Prefect instance and S3 server endpoint. Then you can run :

  ```bash
  docker-compose -f client_s3/docker-compose.yml up weather # Executes weather.py
  ```

Now your flow is registered. You can access the UI to run it.

</details>

### Flow with Docker storage

This method requires our client AND agent containers to have access to Docker so they can package or load the image in which the flow will be executed. We use _Docker in Docker_ for that.

<details>
<summary>Tutorial for (secure) Docker Storage</summary>

#### Start the Docker in Docker agents

Edit registry credentials in `./agent_docker/docker-compose.yml` and run :

```bash
docker-compose -f agent_docker/docker-compose.yml up -d
```

#### Preparing the Registry

A Docker Registry is needed in order to save images that are going to be used by our agents.

1. Open the [`client_docker/config.toml`](./client_docker/config.toml) [`client_docker/docker-compose.yml`](client_docker/docker-compose.yml) files and edit the IP to match your Prefect instance.

2. Generate the authentication credentials for our registry

  ```bash
  sudo apt install apache2-utils # required to generate basic_auth credentials
  cd client_docker/registry/auth && htpasswd -B -c .htpasswd myusername && cd -
  ```

  > To add more users, re-run the previous command **without** the -c option

3. Start the registry

  ```bash
  docker-compose -f client_docker/docker-compose.yml up -d registry
  ```

4. Login to the registry

  You need to allow your Docker daemon to push to this registry. Insert this in your `/etc/docker/daemon.json` (create if needed) :

  ```json
  {
    "insecure-registries": ["172.17.0.1:5000"]
  }
  ```

  Then, run :

  ```bash
  docker login http://172.17.0.1:5000 # with myusername and the password you typed
  ```

  You should see : _Login Succeeded_

#### Registering the flow

We're going to push our Docker image with Python dependencies and register our flow.

1. Build, tag and push the image

  ```bash
  docker build . -f ./client_docker/execution.Dockerfile -t 172.17.0.1:5000/weather/base_image
  ```

  > You **must** prefix your image by the registry URI `172.17.0.1`

  ```bash
  docker push 172.17.0.1:5000/weather/base_image
  ```

2. Register the flow

  Edit registry credentials in `./client_docker/docker-compose.yml` and run :

  ```bash
  docker-compose -f ./client_docker/docker-compose.yml up weather
  ```

Now your flow is registered. You can access the UI to run it.

</details>
