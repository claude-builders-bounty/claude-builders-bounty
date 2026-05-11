#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$ROOT_DIR/tools/generate-changelog/generate_changelog.py" "$@"
