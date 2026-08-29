#!/usr/bin/env bash
set -e

VERSION=${1:-"Unreleased"}
TAG=${2:-""}

if [ -n "$TAG" ]; then
    python3 generate_changelog.py --version "$VERSION" --tag "$TAG"
else
    python3 generate_changelog.py --version "$VERSION"
fi
