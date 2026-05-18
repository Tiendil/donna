#!/usr/bin/bash

set -e

echo "run isort"

./bin/dev.sh uv run isort --check-only ./donna

echo "run black"

./bin/dev.sh uv run black --check ./donna
