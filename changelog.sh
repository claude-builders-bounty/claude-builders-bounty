#!/usr/bin/env bash
set -e

REPO="${1:-.}"

python3 "$(dirname "$0")/changelog-generator.py" "$REPO"
