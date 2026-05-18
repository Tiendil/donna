#!/usr/bin/bash

set -euo pipefail

BUMP_VERSION=${1:-}

if [[ "$BUMP_VERSION" != "minor" && "$BUMP_VERSION" != "patch" ]]; then
    echo "usage: ./bin/release-prepare.sh minor|patch"
    exit 1
fi

echo "Bumping version as $BUMP_VERSION"

NEXT_VERSION=$(./bin/dev.sh uv version --bump "$BUMP_VERSION" --short)
NEXT_VERSION_TAG="release-$NEXT_VERSION"

echo "Update change log"

run_changy() {
    ./bin/dev.sh env UV_NO_SYNC=0 uv run --dev changy "$@"
}

run_changy version create "$NEXT_VERSION"

echo "Generate changelog"

run_changy changelog create

COMMIT_BODY=$(run_changy version show "$NEXT_VERSION")

echo "New version is $NEXT_VERSION"
echo "New version tag $NEXT_VERSION_TAG"

echo "Building Python package"

./bin/dev.sh uv build

echo "Commit changes"

git add pyproject.toml uv.lock CHANGELOG.md changes
git commit -m "Release $NEXT_VERSION" -m "$COMMIT_BODY"
git push

echo "Create tag"

git tag "$NEXT_VERSION_TAG"
git push origin "$NEXT_VERSION_TAG"
