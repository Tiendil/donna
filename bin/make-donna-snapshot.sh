#!/usr/bin/bash

# 1. create .venv if it doesn't exist
# 2. install donna from the local donna directory

if [ ! -d ".venv-donna" ]; then
    python3 -m venv .venv-donna
fi

source .venv-donna/bin/activate

python3 -m pip install ./donna
