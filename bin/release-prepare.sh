#!/usr/bin/bash

set -e

export BUMP_VERSION=$1

echo "Bumping version as $BUMP_VERSION"

export NEXT_VERSION=$(uv version --bump $BUMP_VERSION --short)
export NEXT_VERSION_TAG="release-$NEXT_VERSION"

echo "Install dependencies"

uv sync

echo "Update change log"

uv run changy version create $NEXT_VERSION

echo "Generate changelog"

uv run changy changelog create

export COMMIT_BODY=$(uv run changy version show $NEXT_VERSION)

echo "New version is $NEXT_VERSION"
echo "New version tag $NEXT_VERSION_TAG"

echo "Building Python package"

uv build

echo "Commit changes"

git add -A
git commit -m "Release $NEXT_VERSION" -m "$COMMIT_BODY"
git push

echo "Create tag"

git tag $NEXT_VERSION_TAG
git push origin $NEXT_VERSION_TAG
