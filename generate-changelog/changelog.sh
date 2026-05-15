#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: changelog.sh [--since <ref>] [--output <file>] [--repo <path>]

Generates a Keep-a-Changelog style CHANGELOG from git commits since the last tag
(or from --since). Commit subjects are grouped into Added, Fixed, Changed,
and Removed using conventional-commit prefixes plus simple keyword matching.
EOF
}

REPO="."
SINCE=""
OUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2 ;;
    --since) SINCE="${2:-}"; shift 2 ;;
    --output|-o) OUT="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi

cd "$REPO"

if [[ -z "$SINCE" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    SINCE="$(git describe --tags --abbrev=0)"
  else
    SINCE=""
  fi
fi

if [[ -n "$SINCE" ]]; then
  RANGE="$SINCE..HEAD"
  RANGE_LABEL="since $SINCE"
else
  RANGE="HEAD"
  RANGE_LABEL="from repository history"
fi

COMMITS_FILE="$(mktemp)"
git log --no-merges --pretty=format:'%h%x09%s' $RANGE > "$COMMITS_FILE"
printf '\n' >> "$COMMITS_FILE"
COMMIT_COUNT="$(grep -c '^[0-9a-f]' "$COMMITS_FILE" || true)"
DATE="$(date +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP" "$COMMITS_FILE"' EXIT

category_for() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" introduce"*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*fix*|*bug*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*deprecat*) echo "Removed" ;;
    refactor:*|change:*|changed:*|perf:*|docs:*|test:*|ci:*|chore:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

{
  echo "# Changelog"
  echo
  echo "Generated on $DATE ($RANGE_LABEL)."
  echo
  echo "## Unreleased"
  echo
} > "$TMP"

for category in Added Fixed Changed Removed; do
  echo "### $category" >> "$TMP"
  wrote=0
  while IFS=$'\t' read -r hash subject; do
    [[ -n "${hash:-}" ]] || continue
    if [[ "$(category_for "$subject")" == "$category" ]]; then
      printf -- '- %s (`%s`)\n' "$subject" "$hash" >> "$TMP"
      wrote=1
    fi
  done < "$COMMITS_FILE"
  if [[ "$wrote" -eq 0 ]]; then
    echo "- No entries." >> "$TMP"
  fi
  echo >> "$TMP"
done

mv "$TMP" "$OUT"
echo "Wrote $OUT ($COMMIT_COUNT commits)."
