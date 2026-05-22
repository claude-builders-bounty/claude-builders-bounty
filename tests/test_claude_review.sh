#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="$("$repo_root/bin/claude-review" --diff-file "$repo_root/tests/fixtures/sample.diff")"

grep -q "## PR Review" <<<"$output"
grep -q "### Summary" <<<"$output"
grep -q "### Identified Risks" <<<"$output"
grep -q "Potentially sensitive or destructive added lines" <<<"$output"
grep -q "### Improvement Suggestions" <<<"$output"
grep -q "### Confidence" <<<"$output"

echo "claude-review test passed"
