#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty: $50 — claude-builders-bounty/claude-builders-bounty#1
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO="${2:-.}"

cd "$REPO"

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LATEST_TAG" ]; then
  LATEST_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
  if [ -z "$LATEST_TAG" ]; then
    echo "Error: No commits found." >&2
    exit 1
  fi
  echo "No tags found. Baseline: ${LATEST_TAG:0:7}"
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [Unreleased]" >> "$OUTPUT"
echo "" >> "$OUTPUT"

ADDED=$(mktemp); FIXED=$(mktemp); CHANGED=$(mktemp); REMOVED=$(mktemp); OTHER=$(mktemp)

# Use %n for explicit newlines (git --format doesn't add trailing newline)
git log "${LATEST_TAG}..HEAD" --pretty=format:"%s%n" --no-merges 2>/dev/null | while IFS= read -r msg; do
  msg=$(echo "$msg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$msg" ] && continue

  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(add|feat|new|introduce|implement)'; then
    echo "- $msg" >> "$ADDED"
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|correct|hotfix)'; then
    echo "- $msg" >> "$FIXED"
  elif echo "$lower" | grep -qE '^(remove|drop|delete|deprecate|retire)'; then
    echo "- $msg" >> "$REMOVED"
  elif echo "$lower" | grep -qE '^(change|update|refactor|modify|adjust|tweak|improve|enhance|upgrade|migrate|rework|revise|tune|optimize|clean)'; then
    echo "- $msg" >> "$CHANGED"
  else
    echo "- $msg" >> "$OTHER"
  fi
done

append_section() {
  local name="$1" tmpfile="$2"
  if [ -s "$tmpfile" ]; then
    echo "### $name" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    cat "$tmpfile" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "  ✓ $name: $(wc -l < "$tmpfile") entries"
  fi
}

append_section "Added" "$ADDED"
append_section "Fixed" "$FIXED"
append_section "Changed" "$CHANGED"
append_section "Removed" "$REMOVED"
append_section "Other" "$OTHER"

rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$OTHER"
echo ""
echo "✅ CHANGELOG written to $OUTPUT"
