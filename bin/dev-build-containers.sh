#!/usr/bin/bash

set -e

docker compose build --build-arg UID="$(id -u)" --build-arg GID="$(id -g)" donna
