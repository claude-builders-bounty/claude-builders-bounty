#!/usr/bin/env bash
set -euo pipefail

SCRIPT="skills/generate-changelog/scripts/generate-changelog.sh"

if [[ ! -x "$SCRIPT" ]]; then
  echo "FAIL: script is not executable"
  exit 1
fi

OUTPUT=$(bash "$SCRIPT" --dry-run)

printf '%s' "$OUTPUT" | grep -q "# Changelog" || { echo "FAIL: missing title"; exit 1; }
printf '%s' "$OUTPUT" | grep -q "## \[Unreleased\]" || { echo "FAIL: missing Unreleased section"; exit 1; }
printf '%s' "$OUTPUT" | grep -Eq "### (Added|Fixed|Changed|Removed)|No commits found" || { echo "FAIL: missing category or empty notice"; exit 1; }

tmp=$(mktemp)
bash "$SCRIPT" --output "$tmp" >/dev/null
test -s "$tmp" || { echo "FAIL: output file empty"; exit 1; }
rm -f "$tmp"

echo "PASS: generate-changelog tests passed"
