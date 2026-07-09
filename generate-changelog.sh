#!/usr/bin/env bash
# generate-changelog.sh — thin wrapper around changelog.sh
# Usage: bash generate-changelog.sh [output_file]
#        ./generate-changelog.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/changelog.sh" "$@"
