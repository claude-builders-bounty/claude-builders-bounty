#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
agent="$repo_root/agents/claude-review"

run_case() {
  local pr_url="$1"
  local expected="$2"
  local tmp
  tmp="$(mktemp)"
  trap 'rm -f "$tmp"' RETURN

  "$agent" --pr "$pr_url" > "$tmp"
  diff -u "$repo_root/$expected" "$tmp"
}

run_case "https://github.com/cli/cli/pull/1" "agents/samples/cli-1.md"
run_case "https://github.com/fastapi/fastapi/pull/12592" "agents/samples/fastapi-12592.md"

echo "Verified 2 real PR sample outputs."
