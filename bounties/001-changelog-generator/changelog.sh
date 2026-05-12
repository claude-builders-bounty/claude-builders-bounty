#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--from <tag>] [--output <file>]
set -euo pipefail

FROM_TAG=""
OUTPUT_FILE="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM_TAG="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Determine commit range
if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..HEAD"
elif git describe --tags --abbrev=0 HEAD 2>/dev/null | grep -q .; then
  LAST_TAG=$(git describe --tags --abbrev=0 HEAD 2>/dev/null)
  RANGE="${LAST_TAG}..HEAD"
else
  # No tags — use all commits
  RANGE="HEAD"
fi

TODAY=$(date +%Y-%m-%d)

# Collect commits: "<sha> <subject>"
COMMITS=$(git log "$RANGE" --pretty=format:"%h %s" --no-merges 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range. Nothing to do." >&2
  exit 0
fi

# Categorise a single commit subject
categorise() {
  local msg="$1"
  local prefix="${msg%%:*}"   # everything before the first ":"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  case "$prefix" in
    feat|feature)             echo "Added" ;;
    fix|bugfix|hotfix)        echo "Fixed" ;;
    refactor|perf|style|change|update) echo "Changed" ;;
    remove|deprecate)         echo "Removed" ;;
    chore|ci|build|docs|test) echo "Other" ;;
    *)
      # Keyword heuristics
      if echo "$lower" | grep -qE '(add|new|implement|create|introduce|support)'; then
        echo "Added"
      elif echo "$lower" | grep -qE '(fix|resolve|patch|correct|bug|crash)'; then
        echo "Fixed"
      elif echo "$lower" | grep -qE '(update|refactor|improve|optimise|optimize|rename|move)'; then
        echo "Changed"
      elif echo "$lower" | grep -qE '(remove|delete|deprecate|drop)'; then
        echo "Removed"
      else
        echo "Other"
      fi
      ;;
  esac
}

# Build category arrays
declare -a ADDED FIXED CHANGED REMOVED OTHER

while IFS= read -r line; do
  sha="${line:0:7}"
  subject="${line:8}"
  [[ -z "$subject" ]] && continue

  cat=$(categorise "$subject")
  entry="- ${subject} (\`${sha}\`)"

  case "$cat" in
    Added)   ADDED+=("$entry") ;;
    Fixed)   FIXED+=("$entry") ;;
    Changed) CHANGED+=("$entry") ;;
    Removed) REMOVED+=("$entry") ;;
    *)       OTHER+=("$entry") ;;
  esac
done <<< "$COMMITS"

# Render a section only if non-empty
render_section() {
  local title="$1"; shift
  local entries=("$@")
  if [[ ${#entries[@]} -gt 0 ]]; then
    echo ""
    echo "### $title"
    echo ""
    printf '%s\n' "${entries[@]}"
  fi
}

# Write/update CHANGELOG.md
UNRELEASED_BLOCK="## [Unreleased] — ${TODAY}"
UNRELEASED_BLOCK+=$(render_section "Added"   "${ADDED[@]+"${ADDED[@]}"}")
UNRELEASED_BLOCK+=$(render_section "Fixed"   "${FIXED[@]+"${FIXED[@]}"}")
UNRELEASED_BLOCK+=$(render_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}")
UNRELEASED_BLOCK+=$(render_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}")
UNRELEASED_BLOCK+=$(render_section "Other"   "${OTHER[@]+"${OTHER[@]}"}")

if [[ -f "$OUTPUT_FILE" ]]; then
  # Replace existing [Unreleased] block (idempotent)
  if grep -q "## \[Unreleased\]" "$OUTPUT_FILE"; then
    # Remove old [Unreleased] section, insert new one
    TMP=$(mktemp)
    awk '/^## \[Unreleased\]/{skip=1} /^## \[v?[0-9]/{skip=0} !skip{print}' "$OUTPUT_FILE" > "$TMP"
    { echo "# Changelog"; echo ""; echo "$UNRELEASED_BLOCK"; echo ""; grep -v '^# Changelog' "$TMP" || true; } > "$OUTPUT_FILE"
    rm -f "$TMP"
  else
    # Prepend [Unreleased] section after the title
    TMP=$(mktemp)
    { echo "# Changelog"; echo ""; echo "$UNRELEASED_BLOCK"; echo ""; grep -v '^# Changelog' "$OUTPUT_FILE" || true; } > "$TMP"
    mv "$TMP" "$OUTPUT_FILE"
  fi
else
  { echo "# Changelog"; echo ""; echo "$UNRELEASED_BLOCK"; } > "$OUTPUT_FILE"
fi

echo "Written to $OUTPUT_FILE"
