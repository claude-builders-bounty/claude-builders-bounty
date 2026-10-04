#!/usr/bin/env bash
# Resolve the implementation relative to this wrapper, not the caller's cwd.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/changelog.py" "$@"
