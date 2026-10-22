#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${PYTHON:-}" ]]; then
  exec "$PYTHON" "$script_dir/generate_changelog.py" "$@"
elif command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/generate_changelog.py" "$@"
else
  exec python "$script_dir/generate_changelog.py" "$@"
fi
