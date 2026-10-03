#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$script_dir/changelog.py" "$@"
else
  echo 'Python 3.9+ is required.' >&2
  exit 1
fi
