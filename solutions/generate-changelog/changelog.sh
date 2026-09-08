#!/usr/bin/env bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for python_bin in python3 python; do
  if command -v "$python_bin" >/dev/null 2>&1 &&
    "$python_bin" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    exec "$python_bin" "$script_dir/changelog.py" "$@"
  fi
done
if command -v py >/dev/null 2>&1 &&
  py -3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
  exec py -3 "$script_dir/changelog.py" "$@"
fi
printf '%s\n' 'Python 3.10+ is required. Install Python and retry.' >&2
exit 2
