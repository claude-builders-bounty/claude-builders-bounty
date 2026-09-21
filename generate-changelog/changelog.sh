#!/usr/bin/env bash
set -euo pipefail
script_dir=.
if [[ ${BASH_SOURCE[0]} == */* ]]; then
  script_dir=${BASH_SOURCE[0]%/*}
fi
here="$(cd -- "$script_dir" && pwd)"
exec "${PYTHON:-python3}" "$here/changelog.py" "$@"
