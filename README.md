# modPIPE Streamer Dashboard

An Open Source AGPLv3 Streamer Dashboard to control your Twitch Stream, Chat Bots, AND MORE!

# Early Development
Right now this project does not function as intended and is under ***VERY*** heavy development.

# Starting it up:
## Clone this repository
```
git clone https://github.com/modpipe/modpipe
```

## This project uses Docker Profiles.
The following profiles are present:
    - production:
        - modpipe
        - db
        - static
    - dev:
        - modpipe-dev
        - adminer
    - proxy:
        - traefik
        - whoami

## To run with Traefik as a reverse proxy:
First run you need to create the docker networks:
```
docker network create traefik
docker network create modpipe
```
then bring it up
```
COMPOSE_PROFILES=production,proxy docker compose up -d
```

## To run without traefik:
First run you need to create the docker network:
```
docker network create modpipe
```
then bring it up
```
COMPOSE_PROFILES=production docker compose up -d
```

# To run with adminer and NO proxy:
First run you need to create the docker networks:
```
docker network create traefik
```
then bring it up
```
COMPOSE_PROFILES=dev docker compose up -d
```

# To run with adminer and traefik proxy:
First run you need to create the docker networks:
```
docker network create traefik
docker network create modpipe
```
COMPOSE_PROFILES=dev,proxy docker compose up -d
```