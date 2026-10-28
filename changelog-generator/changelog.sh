#!/usr/bin/env bash
set -euo pipefail

# Resolve the companion file relative to this script, not the target repository.
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/changelog.py" "$@"
