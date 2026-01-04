#!/usr/bin/env bash

# Here we can switch between statically installed donna and its development version

# exec .venv-donna/bin/donna "$@"

cd ./donna && poetry run donna "$@"
