#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
template_dir="$repo_root/templates/nextjs-sqlite-saas"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$tmp_dir/acme-saas"
cp "$template_dir/CLAUDE.md" "$tmp_dir/acme-saas/CLAUDE.md"

assert_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -Eiq "$pattern" "$file"; then
    echo "Contract check failed: $message" >&2
    exit 1
  fi
}

instructions="$tmp_dir/acme-saas/CLAUDE.md"
assert_contains "$instructions" '^# CLAUDE\.md - Next\.js 15 \+ SQLite SaaS$' "title missing"
assert_contains "$instructions" '^## Project Structure$' "project structure section missing"
assert_contains "$instructions" '^## Database And Migration Rules$' "database rules section missing"
assert_contains "$instructions" '^### SQLite Runtime, Storage, And Concurrency$' "SQLite operations section missing"
assert_contains "$instructions" '^## Route Handlers And APIs$' "route handler section missing"
assert_contains "$instructions" '^## Auth And Authorization$' "auth section missing"
assert_contains "$instructions" '^## Testing Rules$' "testing section missing"
assert_contains "$instructions" 'Node\.js driver.*Edge Runtime' "Node-only driver boundary missing"
assert_contains "$instructions" 'persistent writable volume' "persistent storage requirement missing"
assert_contains "$instructions" 'one writer at a time' "SQLite single-writer guidance missing"
assert_contains "$instructions" 'busy timeout' "bounded lock-wait guidance missing"
assert_contains "$instructions" 'requireCurrentUser\(\)' "trusted identity boundary missing"
assert_contains "$instructions" 'Server Actions' "Server Actions guidance missing"
assert_contains "$instructions" 'pin `next`.*15\.5\.28' "patched Next.js minimum-version rule missing"
assert_contains "$instructions" 'better-sqlite3.*@types/better-sqlite3.*devDependency' "conditional better-sqlite3 type dependency missing"

reason_count="$(grep -Ec '\bReason:' "$instructions")"
if [ "$reason_count" -lt 41 ]; then
  echo "Contract check failed: expected at least 41 reasoned rules, found $reason_count" >&2
  exit 1
fi

anti_pattern_count="$(awk '/^## What We Do Not Do/{flag=1; next} /^## Agent Workflow/{flag=0} flag && /^- Do not /{count++} END{print count+0}' "$instructions")"
if [ "$anti_pattern_count" -lt 9 ]; then
  echo "Contract check failed: expected at least 9 anti-patterns, found $anti_pattern_count" >&2
  exit 1
fi

assert_contains "$template_dir/verification/claude-code-greenfield-smoke.md" '^\*\*Status: Protocol only — NOT run in this pull request environment\.' "manual Claude Code test status must not imply it was run"
assert_contains "$template_dir/verification/claude-code-greenfield-smoke.md" 'create-next-app@15\.5\.28' "manual smoke protocol must use the patched Next.js starter"
echo "Template contract check passed: copied instructions, ${reason_count} reasoned rules, ${anti_pattern_count} anti-patterns, and Node/SQLite/auth boundaries verified. Claude Code execution is not performed by this check."
