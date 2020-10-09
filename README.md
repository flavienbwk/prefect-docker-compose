# Prefect - Docker Compose

Make Prefect work with your own simple docker-compose configuration.

This allows you to package your Prefect instance for Kubernetes or offline use.

All `PREFECT_SERVER_*` options are [explained in the official documentation](https://docs.prefect.io/core/concepts/configuration.html#environment-variables) and [listed in the `config.toml` file](https://github.com/PrefectHQ/prefect/blob/master/src/prefect/config.toml).

## Run the server

Please open and edit the [`server/.env`](./server/.env) file. Then you can run :

```console
docker-compose -f server/docker-compose.yml up -d
```

Then, on your host :

```console
pip3 install prefect
prefect server create-tenant --name default --slug default
```

## Run one or multiple agents

Please open and edit the [`agent/config.toml`](./agent/config.toml) file. Then you can run :

You can run the agent on another machine than the one with the Prefect server. Edit the [`agent/.env`](./agent/.env) file for that.

```console
docker-compose -f agent/docker-compose.yml up -d
```

Maybe you want to instanciate multiple agents automatically ?

```console
docker-compose -f agent/docker-compose.yml up -d --scale agent=3 agent
```

## Run your first flow via the Prefect API

Please open the [`scripts/config.toml`](./scripts/config.toml) file and edit the IP to match your Prefect instance. Then you can run :

```console
docker-compose -f scripts/docker-compose.yml up
```

Now your flow is registered. You can access the UI to run some more flows.
