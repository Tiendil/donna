#!/usr/bin/bash

set -e

echo "run autoflake"

./bin/dev.sh poetry run autoflake --check --quiet ./donna

echo "run flake8"

./bin/dev.sh poetry run flake8 ./donna

echo "run mypy"

./bin/dev.sh poetry run mypy --show-traceback ./donna
