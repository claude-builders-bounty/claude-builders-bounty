#!/usr/bin/env bash
set -euo pipefail

python skills/generate-changelog/scripts/generate_changelog.py "$@"
