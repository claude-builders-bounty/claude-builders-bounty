#!/usr/bin/env bash
set -euo pipefail

sample="${1:-samples/claude-review/pr-1381-output.md}"

test -s "$sample"
grep -q '^## Summary$' "$sample"
grep -q '^## Identified risks$' "$sample"
grep -q '^## Improvement suggestions$' "$sample"
grep -q '^## Confidence score$' "$sample"
grep -Eq '^(Low|Medium|High)$' "$sample"

echo "claude-review smoke test passed"
