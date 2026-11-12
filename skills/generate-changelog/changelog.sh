#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Zero dependencies beyond git. Categorises commits into Added / Fixed / Changed / Removed.
#
# Usage:
#   bash changelog.sh                    # commits since the last git tag (or from the first commit)
#   bash changelog.sh --from v1.2.0      # since a specific ref
#   bash changelog.sh --to HEAD --out CHANGELOG.md
#   bash changelog.sh --version 1.4.0    # force the heading instead of "Unreleased"
set -uo pipefail

FROM=""
ROOT_FALLBACK=0
TO="HEAD"
OUT="CHANGELOG.md"
VERSION=""
INCLUDE_MERGES=0

while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM="${2:-}"; shift 2 ;;
    --from=*) FROM="${1#*=}"; shift ;;
    --to) TO="${2:-}"; shift 2 ;;
    --to=*) TO="${1#*=}"; shift ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --out=*) OUT="${1#*=}"; shift ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --version=*) VERSION="${1#*=}"; shift ;;
    --include-merges) INCLUDE_MERGES=1; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repository" >&2; exit 1; }

# Resolve the starting point: explicit --from, else the last tag, else the root commit.
if [ -z "$FROM" ]; then
  FROM="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -z "$FROM" ]; then
    FROM="$(git rev-list --max-parents=0 "$TO" 2>/dev/null | tail -n 1)"
    ROOT_FALLBACK=1
  fi
fi
[ -n "$FROM" ] || { echo "cannot determine a starting commit" >&2; exit 1; }
git rev-parse --verify --quiet "$FROM^{commit}" >/dev/null || { echo "unknown ref: $FROM" >&2; exit 1; }

if [ -n "$VERSION" ]; then
  HEADING="## [$VERSION] - $(date +%Y-%m-%d)"
else
  HEADING="## [Unreleased] - $(date +%Y-%m-%d)"
fi

MERGE_FILTER="--no-merges"
[ "$INCLUDE_MERGES" -eq 1 ] && MERGE_FILTER=""

if [ "${ROOT_FALLBACK:-0}" -eq 1 ]; then
  commit_lines="$(git log $MERGE_FILTER --pretty=format:'%h%x09%s' "$TO" 2>/dev/null)"
else
  commit_lines="$(git log $MERGE_FILTER --pretty=format:'%h%x09%s' "$FROM..$TO" 2>/dev/null)"
fi

ADDED=(); FIXED=(); CHANGED=(); REMOVED=()
while IFS=$'\t' read -r hash subject; do
  [ -n "${hash:-}" ] || continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  body="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
  case "$lower" in
    feat*|feature*|add*|new*)        ADDED+=("$body  ($hash)") ;;
    fix*|bugfix*|hotfix*|patch*)     FIXED+=("$body  ($hash)") ;;
    remove*|delete*|drop*|deprecat*) REMOVED+=("$body  ($hash)") ;;
    *)                               CHANGED+=("$body  ($hash)") ;;
  esac
done <<< "$commit_lines"

emit() {
  local title="$1"; shift
  [ $# -gt 0 ] || return 0
  printf '### %s\n' "$title"
  local item
  for item in "$@"; do printf -- '- %s\n' "$item"; done
  printf '\n'
}

TMP="$(mktemp)"
{
  printf '%s\n\n' "$HEADING"
  if [ $(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} )) -eq 0 ]; then
    printf '_No changes since %s._\n' "$FROM"
  else
    emit "Added"   ${ADDED[@]+"${ADDED[@]}"}
    emit "Changed" ${CHANGED[@]+"${CHANGED[@]}"}
    emit "Fixed"   ${FIXED[@]+"${FIXED[@]}"}
    emit "Removed" ${REMOVED[@]+"${REMOVED[@]}"}
  fi
} > "$TMP"

if [ -f "$OUT" ] && head -n 5 "$OUT" | grep -Fqx "$HEADING"; then
  echo "already up to date: $OUT" >&2
  rm -f "$TMP"
  exit 0
fi

if [ -f "$OUT" ]; then
  { head -n 6 "$TMP"; echo; cat "$OUT"; } > "$OUT.new"; mv "$OUT.new" "$OUT"; rm -f "$TMP"
else
  { printf '# Changelog\n\nAll notable changes to this project are documented here.\n\n'; cat "$TMP"; } > "$OUT"; rm -f "$TMP"
fi

echo "wrote $OUT ($(printf '%s' "$commit_lines" | grep -c . ) commits since $FROM)"