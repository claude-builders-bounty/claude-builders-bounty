#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python3 "$script_dir/scripts/generate_changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$script_dir/scripts/generate_changelog.py" "$@"
else
  echo "Python 3 is required to generate a changelog." >&2
  exit 1
fi
