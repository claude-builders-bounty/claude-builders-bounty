#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--repo /path/to/repo] [--output CHANGELOG.md]
#   If --repo is omitted, uses current directory.
#   If --output is omitted, writes to stdout.

set -euo pipefail

# ── config ──────────────────────────────────────────────────────────────────
REPO="$(pwd)"
OUTPUT=""

# ── parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)    REPO="$2";    shift 2 ;;
    --output)  OUTPUT="$2";  shift 2 ;;
    *) echo "Usage: bash changelog.sh [--repo <path>] [--output <file>]"; exit 1 ;;
  esac
done

cd "$REPO"

# ── determine version range ─────────────────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION_NEXT="$(echo "$LAST_TAG" | sed 's/^v//' | awk -F. '{printf "%d.%d.%d", $1, $2, $3+1}')"
  VERSION_NEXT="v${VERSION_NEXT}"
else
  RANGE="HEAD"
  VERSION_NEXT="v0.1.0"
fi

# ── classify a single commit message ────────────────────────────────────────
classify() {
  local msg="$1"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Conventional commit prefixes
  if echo "$lower" | grep -q '^feat';       then echo "Added";     return 0; fi
  if echo "$lower" | grep -q '^fix';        then echo "Fixed";     return 0; fi
  if echo "$lower" | grep -q '^refactor\|^chore\|^perf'; then echo "Changed";   return 0; fi
  if echo "$lower" | grep -q '^remove\|^rm\b\|^delete\|^drop'; then echo "Removed";   return 0; fi
  if echo "$lower" | grep -q '^deprecat';   then echo "Deprecated"; return 0; fi
  if echo "$lower" | grep -q '^sec\|^audit\|^vuln'; then echo "Security";  return 0; fi

  # Keyword matching (non-cc)
  if echo "$lower" | grep -q -E '\b(add|new|create|implement|introduce)\b';   then echo "Added";     return 0; fi
  if echo "$lower" | grep -q -E '\b(fix|bug|hotfix|patch|correct|repair)\b';  then echo "Fixed";     return 0; fi
  if echo "$lower" | grep -q -E '\b(change|update|improve|refactor|upgrade)\b'; then echo "Changed";   return 0; fi
  if echo "$lower" | grep -q -E '\b(remov|drop|delete|deprecat)\b';           then echo "Removed";   return 0; fi

  # Default
  echo "Changed"
}

# ── gather commits ─────────────────────────────────────────────────────────
COMMITS=$(git log "$RANGE" --oneline --no-merges --pretty=format:"%h|||%s" 2>/dev/null || true)
if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range $RANGE"
  exit 1
fi

# Build categorized entries using temp files (compatible with bash 3)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

for cat in Added Fixed Changed Removed Deprecated Security; do
  : > "$TMPDIR/$cat.txt"
done

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  HASH="${line%%|||*}"
  MSG="${line#*|||}"
  CAT=$(classify "$MSG")
  printf "  - %s (%s)\n" "$MSG" "$HASH" >> "$TMPDIR/$CAT.txt"
done <<< "$COMMITS"

# ── build changelog ────────────────────────────────────────────────────────
DATE=$(date +%Y-%m-%d)

OUTPUT_LINES="# Changelog"
OUTPUT_LINES+=$'\n\n'
OUTPUT_LINES+="## [${VERSION_NEXT}] - ${DATE}"
OUTPUT_LINES+=$'\n\n'

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
if [[ -n "$LAST_TAG" ]]; then
  OUTPUT_LINES+="**${TOTAL} commits** since ${LAST_TAG}"
else
  OUTPUT_LINES+="**${TOTAL} commits** since the beginning"
fi
OUTPUT_LINES+=$'\n\n'

for cat in Added Fixed Changed Removed Deprecated Security; do
  entries=$(cat "$TMPDIR/$cat.txt" 2>/dev/null || true)
  if [[ -n "$entries" ]]; then
    OUTPUT_LINES+="### ${cat}"$'\n'
    OUTPUT_LINES+="${entries}"$'\n'
  fi
done

# Link to compare on GitHub
REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [[ -n "$LAST_TAG" && -n "$REMOTE_URL" ]]; then
  GH_PATH=$(echo "$REMOTE_URL" | sed 's|git@github.com:|github.com/|; s|https://github.com/||; s|\.git$||')
  OUTPUT_LINES+="---"$'\n'
  OUTPUT_LINES+="**Full Changelog**: https://${GH_PATH}/compare/${LAST_TAG}...${VERSION_NEXT}"$'\n'
fi

# ── output ──────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT" ]]; then
  echo "$OUTPUT_LINES" > "$OUTPUT"
  echo "Changelog written to $OUTPUT"
else
  echo "$OUTPUT_LINES"
fi
