# mod|PIPE Streamer Dashboard

An Open Source AGPLv3 Streamer Dashboard to control Bots for Twitch (and possibly other services eventually too)

# Early Development
Right now this project does not function as intended and is under ***VERY*** heavy development.

# Starting it up:
## This project uses Docker Profiles.
The following profiles are present:
    - production:
        - modpipe
        - db
        - static
    - dev:
        - production
        - adminer
    - proxy:
        - traefik
        - whoami

To run with Traefik as a reverse proxy:
```
COMPOSE_PROFILES=production,proxy docker compose up -d
```

To run with an existing traefik proxy:
```
COMPOSE_PROFILES=production docker compose up -d
```

To run with adminer to view the database:
```
COMPOSE_PROFILES=dev docker compose up -d
```

To run with adminer and traefik proxy:
```
COMPOSE_PROFILES=dev,proxy docker compose up -d
```