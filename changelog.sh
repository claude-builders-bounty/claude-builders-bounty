#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Works via `bash changelog.sh` or Claude Code `/generate-changelog`.
# Fetches commits since the last git tag (or since first commit if untagged),
# auto-categorizes into Added / Changed / Fixed / Removed, then writes CHANGELOG.md.
#
# Usage:
#   bash changelog.sh                 # since last tag (or all history if no tags)
#   bash changelog.sh --since=v1.0.0  # override the start ref
#   bash changelog.sh --output=OTHER.md
#   bash changelog.sh --repo=/path
set -euo pipefail

REPO_DIR="."
SINCE=""
OUTPUT="CHANGELOG.md"

for arg in "$@"; do
  case "$arg" in
    --since=*) SINCE="${arg#*=}" ;;
    --output=*) OUTPUT="${arg#*=}" ;;
    --repo=*) REPO_DIR="${arg#*=}" ;;
    --help|-h) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "error: $REPO_DIR is not a git repository" >&2; exit 1
fi

# Resolve start ref: explicit --since, else latest tag, else empty (use HEAD = since first commit).
if [ -z "$SINCE" ]; then
  SINCE="$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [ -z "$SINCE" ]; then
  RANGE="HEAD"
else
  RANGE="${SINCE}..HEAD"
fi

# Categorize a commit subject -> one of: Added Changed Fixed Removed (or empty).
categoriz() {
  local subject="$1"
  local lc="${subject,,}"
  case "$lc" in
    "fix:"*|*"fix:"*|*"bugfix:"*|*"bug:"*) echo "Fixed"; return ;;
    "feat:"*|*"feature:"*|*"add:"*|*"added:"*) echo "Added"; return ;;
    "change:"*|*"changed:"*|*"update:"*|*"refactor:"*|*"perf:"*) echo "Changed"; return ;;
    "remove:"*|*"removed:"*|*"delete:"*|*"deprecat:"*) echo "Removed"; return ;;
  esac
  case "$lc" in
    *fix*|*bug*|*crash*|*error*|*exception*|*broken*|*resets*) echo "Fixed"; return ;;
    *add*|*new*|*introduc*|*implement*|*build*|*initial*|*create*) echo "Added"; return ;;
    *change*|*update*|*refactor*|*modif*|*switch*|*improv*|*replace*|*adjust*|*tweak*) echo "Changed"; return ;;
    *remove*|*delete*|*drop*|*deprecat*|*rm*) echo "Removed"; return ;;
  esac
  echo ""
}

NEW_VERSION="$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || echo "0.1.0")"
TODAY="$(date +%Y-%m-%d)"
COMMIT_COUNT="$(git -C "$REPO_DIR" rev-list "${RANGE}" --count 2>/dev/null || echo 0)"

mapfile -t ROWS < <(
  git -C "$REPO_DIR" log "$RANGE" --reverse --pretty=format:'%H|||%s|||%an' 2>/dev/null || true
)

declare -A BUCKETS=(
  ["Added"]=""
  ["Changed"]=""
  ["Fixed"]=""
  ["Removed"]=""
)
OTHER=""

for row in "${ROWS[@]}"; do
  sha="${row%%|||*}"
  rest="${row#*|||}"
  subject="${rest%%|||*}"
  author="${rest#*|||}"

  cat="$(categoriz "$subject")"
  bullet="- ${subject}"
  if [ -n "$cat" ]; then
    BUCKETS["$cat"]+="${bullet}"$'\n'
  else
    OTHER+="${bullet}"$'\n'
  fi
done

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$NEW_VERSION" "$TODAY"
  printf '<!-- Generated from git history (range: `%s`, %s commits) -->\n\n' "$RANGE" "$COMMIT_COUNT"
  for sec in "Added" "Changed" "Fixed" "Removed"; do
    body="${BUCKETS[$sec]}"
    if [ -n "$body" ]; then
      printf '### %s\n%s\n' "$sec" "$body"
    fi
  done
  if [ -n "$OTHER" ]; then
    printf '### Changed\n%s\n' "$OTHER"
  fi
  printf '<!-- End -->\n'
} > "$OUTPUT"

echo "Wrote $OUTPUT from '$RANGE' ($COMMIT_COUNT commits, $(wc -l < "$OUTPUT") lines)."
