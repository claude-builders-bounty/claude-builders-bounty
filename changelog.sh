#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "Python 3 is required to generate the changelog." >&2
  exit 1
fi

exec "$python_bin" "$script_dir/scripts/generate_changelog.py" "$@"
