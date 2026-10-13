#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/generate_changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$script_dir/generate_changelog.py" "$@"
else
  printf 'Error: Python 3 is required.\n' >&2
  exit 1
fi
