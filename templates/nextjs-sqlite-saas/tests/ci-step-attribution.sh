#!/usr/bin/env bash
# Attribution guard — reject agent trailers in template sources and commits.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TEMPLATE_DIR="${REPO_ROOT}/templates/nextjs-sqlite-saas"

cd "$REPO_ROOT"

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  "${TEMPLATE_DIR}/" \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in template sources'
  exit 1
fi

if git log -1 --format='%B' | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

template_commit_messages="$(
  git log upstream/main..HEAD --format='%B' -- templates/nextjs-sqlite-saas/ 2>/dev/null || true
)"
if printf '%s\n' "$template_commit_messages" | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution strings found in template commit messages'
  exit 1
fi
