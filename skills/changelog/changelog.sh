#!/usr/bin/env bash
# Requires git and Python 3.10+; installs nothing and calls no model/API.
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python3}" "$SCRIPT_DIR/generate_changelog.py" "$@"
