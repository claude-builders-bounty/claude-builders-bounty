#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   ./changelog.sh              # From last tag to HEAD
#   ./changelog.sh v1.0.0       # From a specific tag
#   ./changelog.sh v1.0.0 v2.0.0  # Between two tags
#
# Categories: Added, Changed, Fixed, Removed, Deprecated, Security
#
set -euo pipefail

# ── colours for terminal output (disabled when piped) ──
if [ -t 1 ]; then
  BOLD='\033[1m'; GREEN='\033[32m'; YELLOW='\033[33m'; CYAN='\033[36m'; NC='\033[0m'
else
  BOLD='' GREEN='' YELLOW='' CYAN='' NC=''
fi

# ── resolve range ──
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || { echo "Not a git repo." >&2; exit 1; })"

if [ $# -eq 0 ]; then
  # No args: last tag → HEAD
  FROM_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [ -z "$FROM_TAG" ]; then
    # No tags at all — use the first commit
    FIRST_COMMIT="$(git rev-list --max-parents=0 HEAD)"
    FROM_TAG="$FIRST_COMMIT"
    RANGE_LABEL="Initial release"
  else
    RANGE_LABEL="$FROM_TAG"
  fi
  RANGE="${FROM_TAG}..HEAD"
elif [ $# -eq 1 ]; then
  FROM_TAG="$1"
  RANGE_LABEL="$FROM_TAG"
  RANGE="${FROM_TAG}..HEAD"
else
  FROM_TAG="$1"
  TO_TAG="$2"
  RANGE_LABEL="$FROM_TAG...$TO_TAG"
  RANGE="${FROM_TAG}..${TO_TAG}"
fi

# ── grab commits and classify ──
declare -a ADDED=() CHANGED=() FIXED=() REMOVED=() DEPRECATED=() SECURITY=() OTHER=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  hash="$(echo "$line" | cut -d'|' -f1)"
  subj="$(echo "$line" | cut -d'|' -f2-)"

  # strip leading lower-case conventional prefix  (feat|fix|refactor|chore|docs|style|test|perf|build|ci|revert)(scope)?(!)?: 
  normalized="$(echo "$subj" | sed -E 's/^[a-z]+(\([^)]*\))?!?:\s*//')"

  lower="$(echo "$subj" | tr '[:upper:]' '[:lower:]')"

  if echo "$lower" | grep -qE '^(feat|add|implement|introduce|create|support|new )'; then
    ADDED+=("$hash $normalized")
  elif echo "$lower" | grep -qE '^(fix|bugfix|patch|resolve|close|repair|hotfix)'; then
    FIXED+=("$hash $normalized")
  elif echo "$lower" | grep -qE '^(remove|delete|drop|eliminate|strip)'; then
    REMOVED+=("$hash $normalized")
  elif echo "$lower" | grep -qE '^(deprecated|deprecate)'; then
    DEPRECATED+=("$hash $normalized")
  elif echo "$lower" | grep -qE '^(security|cve|vulnerability|xss|csrf|injection)'; then
    SECURITY+=("$hash $normalized")
  elif echo "$lower" | grep -qE '^(change|update|modify|refactor|improve|enhance|rename|migrate|upgrade|bump|move|rearrange|reorganize|reorder|swap|replace)'; then
    CHANGED+=("$hash $normalized")
  else
    OTHER+=("$hash $normalized")
  fi
done < <(git log --format="%h|%s" "$RANGE" 2>/dev/null)

TOTAL=$((${#ADDED[@]}+${#CHANGED[@]}+${#FIXED[@]}+${#REMOVED[@]}+${#DEPRECATED[@]}+${#SECURITY[@]}+${#OTHER[@]}))
if [ "$TOTAL" -eq 0 ]; then
  echo -e "${YELLOW}No commits found in range ${RANGE}${NC}" >&2
  exit 0
fi

# ── date for header ──
TODAY="$(date +%Y-%m-%d)"

# resolve a human-friendly version label
if [ $# -eq 2 ]; then
  VERSION="$TO_TAG"
elif [ $# -eq 1 ]; then
  VERSION="HEAD (from $FROM_TAG)"
else
  # try to guess next version
  LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [ -n "$LATEST_TAG" ]; then
    # bump patch
    VERSION="$(echo "$LATEST_TAG" | sed -E 's/^v?([0-9]+\.[0-9]+\.)[0-9]+$/\1/' )"
    if [ "$VERSION" = "$LATEST_TAG" ]; then
      VERSION="Unreleased"
    else
      NEXT_PATCH="$(echo "$LATEST_TAG" | grep -oE '[0-9]+$')"
      VERSION="${VERSION}$((NEXT_PATCH + 1))"
    fi
  else
    VERSION="Unreleased"
  fi
fi

# ── build output ──
OUT=""

section() {
  local title="$1"; shift
  local -n arr="$1"
  if [ ${#arr[@]} -eq 0 ]; then return; fi
  OUT+="### $title"$'\n'$'\n'
  for entry in "${arr[@]}"; do
    local h="${entry%% *}"
    local m="${entry#* }"
    OUT+="- $m ($h)"$'\n'
  done
  OUT+=$'\n'
}

OUT+="# Changelog"$'\n'$'\n'
OUT+="## [$VERSION] - $TODAY"$'\n'$'\n'

section "Added"      ADDED
section "Changed"    CHANGED
section "Deprecated" DEPRECATED
section "Removed"    REMOVED
section "Fixed"      FIXED
section "Security"   SECURITY
section "Other"      OTHER

# ── write to CHANGELOG.md ──
TARGET="$REPO_ROOT/CHANGELOG.md"

if [ -f "$TARGET" ]; then
  # prepend before the first existing heading
  HEADER_LINE="$(grep -n '^# Changelog' "$TARGET" | head -1 | cut -d: -f1)"
  if [ -n "$HEADER_LINE" ]; then
    # remove old header, keep the rest
    REST="$(tail -n +"$((HEADER_LINE + 1))" "$TARGET")"
    printf '%s\n%s\n' "$OUT" "$REST" > "$TARGET"
  else
    printf '%s\n%s\n' "$OUT" "$(cat "$TARGET")" > "$TARGET"
  fi
else
  printf '%s' "$OUT" > "$TARGET"
fi

# ── summary ──
echo -e "${BOLD}${GREEN}CHANGELOG.md generated!${NC} ($TOTAL commits in range $RANGE_LABEL)"
echo -e "  ${CYAN}Added:${NC}       ${#ADDED[@]}"
echo -e "  ${CYAN}Changed:${NC}     ${#CHANGED[@]}"
echo -e "  ${CYAN}Fixed:${NC}       ${#FIXED[@]}"
echo -e "  ${CYAN}Removed:${NC}     ${#REMOVED[@]}"
echo -e "  ${CYAN}Deprecated:${NC}  ${#DEPRECATED[@]}"
echo -e "  ${CYAN}Security:${NC}    ${#SECURITY[@]}"
echo -e "  ${CYAN}Other:${NC}       ${#OTHER[@]}"
