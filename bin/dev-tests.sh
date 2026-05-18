#!/usr/bin/bash

set -e

echo "run tests"

./bin/dev.sh poetry run pytest donna -o cache_dir=/tmp/donna-pytest-cache
