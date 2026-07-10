#!/usr/bin/env bash
# Thin wrapper so `bash changelog.sh` works from the repo root.
exec "$(cd "$(dirname "$0")" && pwd)/generate-changelog/changelog.sh" "$@"
