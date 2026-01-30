#!/usr/bin/env bash

# Here we can switch between statically installed donna and its development version

# exec .venv-donna/bin/donna "$@"

ROOT_DIR="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT_DIR"
poetry run donna "$@"
