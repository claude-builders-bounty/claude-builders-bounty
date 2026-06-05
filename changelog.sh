#!/usr/bin/env bash
# generate-changelog — Auto-generate CHANGELOG.md from git history
# Usage: ./changelog.sh [--since <tag>] [--output <file>]
set -euo pipefail

OUTPUT="${OUTPUT:-CHANGELOG.md}"
SINCE="${SINCE:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
REPO_URL="$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's/^git@github\.com:/https:\/\/github.com\//')"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

# --- Fetch commits ---
if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
else
  # No tags yet — use all commits
  RANGE="HEAD"
fi

COMMITS=$(git log "$RANGE" --pretty=format:'%s' 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since ${SINCE:-the beginning}."
  exit 0
fi

# --- Categorize ---
declare -a ADDED FIXED CHANGED REMOVED

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg="${line#"${line%%[![:space:]]*}"}"  # trim leading whitespace

  if   [[ "$msg" =~ ^[Ff]eat[:\(]|^[Aa]dd[:\(] ]];   then ADDED+=("$msg")
  elif [[ "$msg" =~ ^[Ff]ix[:\(]|^[Bb]ug[:\(]|^[Hh]otfix[:\(] ]]; then FIXED+=("$msg")
  elif [[ "$msg" =~ ^[Rr]emove[:\(]|^[Dd]elete[:\(]|^[Dd]rop[:\(] ]]; then REMOVED+=("$msg")
  elif [[ "$msg" =~ ^[Cc]hore[:\(]|^[Rr]efactor[:\(]|^[Ss]tyle[:\(]|^[Pp]erf[:\(]|^[Dd]ocs[:\(]|^[Tt]est[:\(]|^[Cc]i[:\(]|^[Bb]uild[:\(] ]]; then CHANGED+=("$msg")
  else CHANGED+=("$msg")  # default bucket
  fi
done <<< "$COMMITS"

# --- Generate output ---
VERSION="${SINCE:-initial}"
TODAY=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] — ${TODAY}"
  echo ""

  section() {
    local title="$1"; shift
    local -n arr=$1
    [[ ${#arr[@]} -eq 0 ]] && return
    echo "### $title"
    echo ""
    for item in "${arr[@]}"; do
      echo "- $item"
    done
    echo ""
  }

  section "Added"   ADDED
  section "Fixed"   FIXED
  section "Changed" CHANGED
  section "Removed" REMOVED

} > "$OUTPUT"

# --- Summary ---
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
echo "Done. $TOTAL commits categorized → $OUTPUT"
echo "  Added:   ${#ADDED[@]}"
echo "  Fixed:   ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
