#!/usr/bin/env bash
# =============================================================================
# generate-changelog.sh — Generate CHANGELOG.md from git history
#
# Usage: bash changelog.sh [options]
#   -o FILE   Output file (default: CHANGELOG.md)
#   -t TAG    Generate since this tag (auto-detected if omitted)
#   -r REPO   Path to git repo (default: current directory)
#   -a        Include all commits (not just since last tag)
#   -h        Show help
# =============================================================================

set -euo pipefail

# --- Defaults ---
OUTPUT="CHANGELOG.md"
SINCE_TAG=""
REPO_DIR="."
ALL_COMMITS=false

# --- Parse args ---
while getopts "o:t:r:ah" opt; do
  case "$opt" in
    o) OUTPUT="$OPTARG" ;;
    t) SINCE_TAG="$OPTARG" ;;
    r) REPO_DIR="$OPTARG" ;;
    a) ALL_COMMITS=true ;;
    h)
      sed -n '2,/^# ===/{ /^#/d; s/^# //; p }' "$0"
      exit 0
      ;;
    *) echo "Unknown option: -$opt" >&2; exit 1 ;;
  esac
done

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository — $REPO_DIR" >&2
  exit 1
fi

# --- Detect last tag ---
if [[ -z "$SINCE_TAG" ]] && [[ "$ALL_COMMITS" == false ]]; then
  SINCE_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

# --- Build git log range ---
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  VERSION_LABEL="## [Unreleased] (since ${SINCE_TAG})"
else
  RANGE="HEAD"
  VERSION_LABEL="## [Unreleased]"
fi

# --- Category detection ---
declare -A CATEGORY_MAP
CATEGORY_MAP[Added]="feat add new implement"
CATEGORY_MAP[Fixed]="fix bug patch resolve close closes closed fixes fixed"
CATEGORY_MAP[Changed]="change update refactor improve modify chore perf performance"
CATEGORY_MAP[Removed]="remove delete deprecate drop"

categorize() {
  local msg="$1"
  local lower
  lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"

  for category in "Added" "Fixed" "Changed" "Removed"; do
    for keyword in ${CATEGORY_MAP[$category]}; do
      # Match prefix like "feat:", "fix(auth):", or standalone word
      if echo "$lower" | grep -qE "^${keyword}[\(:\s]|^${keyword}$|\b${keyword}\b"; then
        echo "$category"
        return
      fi
    done
  done
  echo "Other Changes"
}

# --- Collect commits ---
declare -A SECTIONS
ORDER=("Added" "Fixed" "Changed" "Removed" "Other Changes")
for cat in "${ORDER[@]}"; do
  SECTIONS["$cat"]=""
done

while IFS='|' read -r hash date message; do
  [[ -z "$hash" ]] && continue
  short_hash="${hash:0:7}"
  category="$(categorize "$message")"
  line="- ${message} (${short_hash})"
  SECTIONS["$category"]="${SECTIONS[$category]}${line}"$'\n'
done < <(git log --format='%H|%ad|%s' --date=short $RANGE 2>/dev/null)

# --- Build output ---
{
  echo "# Changelog"
  echo ""
  echo "${VERSION_LABEL}"
  echo ""

  has_content=false
  for cat in "${ORDER[@]}"; do
    if [[ -n "${SECTIONS[$cat]}" ]]; then
      echo "### ${cat}"
      echo ""
      echo -n "${SECTIONS[$cat]}"
      echo ""
      has_content=true
    fi
  done

  if [[ "$has_content" == false ]]; then
    echo "_No commits found._"
    echo ""
  fi
} > "$OUTPUT"

echo "✅ Changelog written to: $OUTPUT"
echo "   Commits parsed: $(git log --oneline $RANGE 2>/dev/null | wc -l | tr -d ' ')"
if [[ -n "$SINCE_TAG" ]]; then
  echo "   Since tag: $SINCE_TAG"
else
  echo "   Scope: all commits (no tags found)"
fi
