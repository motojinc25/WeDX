# Setup Azure IoT Edge

### Azure Container Registry 

Log in to a Docker registry

```bash
$ docker login -u <ACR username> -p <ACR password> <ACR login server>
```

Set Azure Container Registry environment

```bash
$ cat > .env
CONTAINER_REGISTRY_ADDRESS=""
CONTAINER_REGISTRY_USERNAME=""
CONTAINER_REGISTRY_PASSWORD=""
```
