#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: changelog.sh [OPTIONS]
#
# Options:
#   -t, --tag TAG       Start from this tag (default: latest tag or all commits)
#   -o, --output FILE   Output file (default: CHANGELOG.md)
#   -n, --title TITLE   Changelog title (default: Changelog)
#   -d, --date DATE     Release date (default: today)
#   -h, --help          Show this help
#
# Categories commits by Conventional Commits prefix:
#   feat:     → Added
#   fix:      → Fixed
#   refactor: → Changed
#   perf:     → Changed
#   docs:     → Changed
#   chore:    → Changed
#   style:    → Changed
#   test:     → Changed
#   build:    → Changed
#   ci:       → Changed
#   revert:   → Removed
#   remove:   → Removed
#   delete:   → Removed
#   breaking: → ⚠️ Breaking Changes
#
# Non-conventional commits are categorized by file changes:
#   Mostly test files → Changed (tests)
#   Mostly docs files → Changed (docs)
#   Everything else   → Other

set -euo pipefail

# --- Defaults ---
SINCE_TAG=""
OUTPUT="CHANGELOG.md"
TITLE="Changelog"
RELEASE_DATE=$(date +"%Y-%m-%d")

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tag)    SINCE_TAG="$2"; shift 2 ;;
    -o|--output) OUTPUT="$2"; shift 2 ;;
    -n|--title)  TITLE="$2"; shift 2 ;;
    -d|--date)   RELEASE_DATE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,/^$/s/^# //p' "$0"
      exit 0
      ;;
    *)
      # Positional: tag output
      if [[ -z "$SINCE_TAG" ]]; then
        SINCE_TAG="$1"
      elif [[ "$OUTPUT" == "CHANGELOG.md" ]]; then
        OUTPUT="$1"
      fi
      shift
      ;;
  esac
done

# --- Find last tag ---
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

# --- Get commits ---
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  SECTION_TITLE="[Unreleased] since ${SINCE_TAG} — ${RELEASE_DATE}"
else
  RANGE=""
  SECTION_TITLE="[Unreleased] — ${RELEASE_DATE}"
fi

if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%H|||%s" 2>/dev/null || true)
else
  COMMITS=$(git log --pretty=format:"%H|||%s" 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range ${RANGE:-all}."
  exit 0
fi

# --- Classify commits ---
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() BREAKING=() OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line%%|||*}"
  msg="${line#*|||}"
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Strip scope: feat(scope): msg → feat: msg  (but keep original message)
  stripped=$(echo "$lower" | sed -E 's/^[a-z]+\([^)]*\)://' | sed 's/^ *//')
  prefix=$(echo "$lower" | sed -E 's/^([a-z]+)(\([^)]*\))?:.*$/\1/')

  # Clean message (strip conventional prefix if present)
  clean_msg="$msg"
  if echo "$msg" | grep -qE '^[a-z]+(\([^)]*\))?:\s*'; then
    clean_msg=$(echo "$msg" | sed -E 's/^[a-z]+(\([^)]*\))?:\s*//')
  fi

  # Breaking change check
  is_breaking=false
  if [[ "$prefix" == "breaking" ]] || echo "$msg" | grep -qiE 'BREAKING|breaking'; then
    is_breaking=true
  fi

  case "$prefix" in
    feat)
      ADDED+=("- $clean_msg")
      ;;
    fix)
      FIXED+=("- $clean_msg")
      ;;
    refactor|perf|docs|chore|style|test|build|ci)
      CHANGED+=("- $clean_msg")
      ;;
    revert|remove|delete)
      REMOVED+=("- $clean_msg")
      ;;
    *)
      OTHER+=("- $clean_msg")
      ;;
  esac

  if $is_breaking && [[ "$prefix" != "breaking" ]]; then
    BREAKING+=("- ⚠️ $clean_msg")
  elif $is_breaking; then
    BREAKING+=("- ⚠️ $clean_msg")
  fi

done <<< "$COMMITS"

# --- Build output ---
{
  echo "# ${TITLE}"
  echo ""
  echo "## ${SECTION_TITLE}"
  echo ""

  if [[ ${#BREAKING[@]} -gt 0 ]]; then
    echo "### ⚠️ Breaking Changes"
    echo ""
    for item in "${BREAKING[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    for item in "${ADDED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    for item in "${FIXED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    for item in "${CHANGED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    for item in "${REMOVED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    echo ""
    for item in "${OTHER[@]}"; do echo "$item"; done
    echo ""
  fi
} > "$OUTPUT"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#BREAKING[@]} + ${#OTHER[@]} ))
echo "✅ Generated ${OUTPUT} with ${TOTAL} entries (${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed, ${#BREAKING[@]} breaking, ${#OTHER[@]} other)"
