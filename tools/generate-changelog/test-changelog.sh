#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"
tmp_output="$(mktemp)"
trap 'rm -f "$tmp_output"' EXIT

bash "$repo_root/tools/generate-changelog/changelog.sh" "$tmp_output" >/dev/null

grep -q '^# Changelog$' "$tmp_output"
grep -q '^### Added$' "$tmp_output"
grep -q '^### Fixed$' "$tmp_output"
grep -q '^### Changed$' "$tmp_output"
grep -q '^### Removed$' "$tmp_output"

echo "generate-changelog smoke test passed"
