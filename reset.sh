#!/usr/bin/env bash
docker compose down
git reset HEAD --hard
git clean -fd
git pull
if [ -f /usr/local/docker/nightbot-web.adjust ]; then
    cat ../*.adjust >> docker-compose.yml
fi
docker compose build
docker compose up -d
docker compose logs -f