#!/usr/bin/bash

set -e

echo "run isort"

./bin/dev.sh poetry run isort --check-only ./donna

echo "run black"

./bin/dev.sh poetry run black --check ./donna
