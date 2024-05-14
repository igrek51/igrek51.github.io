# Docker cheatsheet

## Logs in time window
```bash
docker logs postgres -t --since 2018-11-29T12:21:00 --until 2018-11-29T12:22:00 2>&1 >/dev/null | grep -n "phrase"
```

## List Docker registry
```sh
curlie http://localhost:5000/v2/_catalog
curlie http://localhost:5000/v2/my-name/postgres/tags/list
curlie http://localhost:5000/v2/my-name/postgres/manifests/latest
```
## Remove image from Docker registry
```sh
curlie -X DELETE http://localhost:5000/v2/my-name/postgres/manifests/latest
```
if `--env=REGISTRY_STORAGE_DELETE_ENABLED=true`

## Clear Docker local registry, containers & images
```sh
sudo docker rm -f `sudo docker ps -a -q`
sudo docker rmi -f `sudo docker images -q`
```

## runlike: check docker run command
```sh
pip install runlike
runlike postgres
```

## Enter shell on exited container
```sh
CONTAINER=postgres
docker rmi -f tmp
docker commit $CONTAINER tmp
docker run -it --rm --entrypoint=bash tmp
```

## Declutter disk usage
```sh
docker image prune
docker system prune -a --volumes
docker system df
```

## History of commands (layers)
```sh
docker history postgres:10
```

## Explore image layers
```sh
docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest \
    postgres:10
```

## Manage docker resources
```sh
docker run --rm -it -p 8001:8000 -p 9001:9000 --name=portainer -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer-ce
localhost:9001
```

## Am I in Docker?
```sh
cat /proc/1/cgroup
# root paths or /docker/...
```

## Gain root access with docker
```sh
docker run -it --rm -v `pwd`:`pwd` -w `pwd` ubuntu bash
```

## Update docker container restart policy
```sh
docker update --restart=unless-stopped reverseproxy
```

## Attach to stdin (debugger)
Attach to stdin of a `-it` container:
```sh
docker attach CONTAINER
detach with sequence: Ctrl^P, Ctrl^Q
```
