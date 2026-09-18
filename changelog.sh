#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for interpreter in "${PYTHON:-python3}" python; do
  if "$interpreter" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    exec "$interpreter" "$script_dir/tools/changelog.py" "$@"
  fi
done
printf '%s\n' 'changelog: Python 3.9+ is required (set PYTHON to its executable if needed)' >&2
exit 1
