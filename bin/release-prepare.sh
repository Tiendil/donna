#!/usr/bin/bash

set -e

export BUMP_VERSION=$1

echo "Bumping version as $BUMP_VERSION"

export NEXT_VERSION=$(poetry version $BUMP_VERSION --short)
export NEXT_VERSION_TAG="release-$NEXT_VERSION"

echo "Install dependencies"

poetry install

echo "Update change log"

poetry run changy version create $NEXT_VERSION

echo "Generate changelog"

poetry run changy changelog create

export COMMIT_BODY=$(poetry run changy version show $NEXT_VERSION)

echo "New version is $NEXT_VERSION"
echo "New version tag $NEXT_VERSION_TAG"

echo "Building Python package"

poetry build

echo "Commit changes"

git add -A
git commit -m "Release $NEXT_VERSION" -m "$COMMIT_BODY"
git push

echo "Create tag"

git tag $NEXT_VERSION_TAG
git push origin $NEXT_VERSION_TAG
