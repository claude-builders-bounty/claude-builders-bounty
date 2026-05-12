#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="$("$root/bin/claude-review" --diff-file "$root/tests/sample.diff" --mode local)"

grep -Fq "## Summary" <<<"$output"
grep -Fq "## Identified Risks" <<<"$output"
grep -Fq "## Improvement Suggestions" <<<"$output"
grep -Fq "## Confidence Score" <<<"$output"
grep -Eq "^(Low|Medium|High)$" <<<"$output"

prompt="$("$root/bin/claude-review" --diff-file "$root/tests/sample.diff" --mode prompt)"
grep -Fq "name: pr-reviewer" <<<"$prompt"
grep -Fq "Diff:" <<<"$prompt"

echo "claude-review tests passed"
