#!/usr/bin/env bash
set -euo pipefail
case "${BASH_SOURCE[0]}" in
  */*) script_dir="${BASH_SOURCE[0]%/*}" ;;
  *) script_dir="." ;;
esac
script_dir="$(cd -- "$script_dir" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/changelog.py" "$@"
fi
exec python "$script_dir/changelog.py" "$@"
