#!/usr/bin/env bash
# generate-changelog.sh — generate a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [since-tag] [--output CHANGELOG.md]
#
# Features:
# - Fetches commits since the last git tag (or a given tag)
# - Auto-categorizes into Added / Fixed / Changed / Removed
# - Outputs a properly formatted CHANGELOG.md
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# --- Argument parsing -------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      OUTPUT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: bash generate-changelog.sh [since-tag] [--output CHANGELOG.md]"
      echo ""
      echo "Arguments:"
      echo "  since-tag    Start point (tag name). Defaults to the latest tag."
      echo "  --output     Output file (default: CHANGELOG.md)"
      exit 0
      ;;
    *)
      SINCE_TAG="$1"
      shift
      ;;
  esac
done

# --- Resolve the start point ------------------------------------------------
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  HEADER="## Changes since ${SINCE_TAG} ($(date +%Y-%m-%d))"
else
  RANGE="HEAD"
  HEADER="## Changelog ($(date +%Y-%m-%d))"
fi

# --- Collect commits ---------------------------------------------------------
# Skip merge commits (their subject is duplicated by the merged commits)
COMMITS="$(git log "$RANGE" --no-merges --pretty=format:'%H%x09%s' 2>/dev/null || git log --no-merges --pretty=format:'%H%x09%s')"

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since ${SINCE_TAG:-the beginning of history}. Nothing to do."
  exit 0
fi

# --- Categorize by conventional commit prefixes -------------------------------
added=()
fixed=()
changed=()
removed=()
other=()

classify() {
  local subject="$1"
  local lower
  lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat*|add*|implement*|support*|create*)
      added+=("$subject") ;;
    fix*|bug*|patch*|repair*|resolve*|hotfix*)
      fixed+=("$subject") ;;
    refactor*|update*|improve*|change*|enhance*|optimize*|move*|rename*|bump*|migrate*)
      changed+=("$subject") ;;
    remove*|delete*|drop*|deprecate*)
      removed+=("$subject") ;;
    *)
      other+=("$subject") ;;
  esac
}

format_entry() {
  # Strip conventional-commit prefix and issue refs; capitalize first letter
  local subject="$1"
  subject="$(echo "$subject" | sed -E 's/^(feat|fix|chore|refactor|docs|style|test|perf|build|ci)(\([a-zA-Z0-9_-]+\))?!?:[[:space:]]*//I')"
  subject="$(echo "$subject" | sed -E 's/[[:space:]]*\(#([0-9]+)\)//')"
  echo "$subject"
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  clean="$(format_entry "$subject")"
  entry="- ${clean} (\`${hash:0:7}\`)"
  classify_subject="$entry"
  lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat*|add*|implement*|support*|create*) added+=("$entry") ;;
    fix*|bug*|patch*|repair*|resolve*|hotfix*) fixed+=("$entry") ;;
    refactor*|update*|improve*|change*|enhance*|optimize*|move*|rename*|bump*|migrate*) changed+=("$entry") ;;
    remove*|delete*|drop*|deprecate*) removed+=("$entry") ;;
    *) other+=("$entry") ;;
  esac
done < <(echo "$COMMITS")

# --- Render -------------------------------------------------------------------
render_section() {
  local name="$1"
  shift
  local arr=("$@")
  if [[ ${#arr[@]} -eq 0 ]]; then
    return
  fi
  echo "### $name"
  printf '%s\n' "${arr[@]}" | sort -u
  echo ""
}

{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""
  if [[ ${#added[@]} -eq 0 && ${#fixed[@]} -eq 0 && ${#changed[@]} -eq 0 && ${#removed[@]} -eq 0 && ${#other[@]} -eq 0 ]]; then
    echo "_No changes found._"
    exit 0
  fi
  render_section "Added" "${added[@]}"
  render_section "Fixed" "${fixed[@]}"
  render_section "Changed" "${changed[@]}"
  render_section "Removed" "${removed[@]}"
  render_section "Other" "${other[@]}"
} > "$OUTPUT"

echo "CHANGELOG written to $OUTPUT"
