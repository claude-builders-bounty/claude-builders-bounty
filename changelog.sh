#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty: $50 — claude-builders-bounty/claude-builders-bounty#1
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO="${2:-.}"

cd "$REPO"

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LATEST_TAG" ]; then
  if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "Error: No commits found." >&2
    exit 1
  fi
  echo "No tags found. Including all commits."
  RANGE=()
else
  RANGE=("${LATEST_TAG}..HEAD")
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [Unreleased]" >> "$OUTPUT"
echo "" >> "$OUTPUT"

ADDED=$(mktemp); FIXED=$(mktemp); CHANGED=$(mktemp); REMOVED=$(mktemp)

# Use %n for explicit newlines (git --format doesn't add trailing newline)
git log "${RANGE[@]}" --pretty=format:"%s%n" --no-merges 2>/dev/null | while IFS= read -r msg; do
  msg=$(echo "$msg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$msg" ] && continue

  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(add|feat|feature|new|introduce|implement)'; then
    echo "- $msg" >> "$ADDED"
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|correct|hotfix)'; then
    echo "- $msg" >> "$FIXED"
  elif echo "$lower" | grep -qE '^(remove|drop|delete|deprecate|retire)'; then
    echo "- $msg" >> "$REMOVED"
  else
    # Everything not clearly added/fixed/removed is grouped as Changed so
    # the output stays within the requested four Keep-a-Changelog sections.
    echo "- $msg" >> "$CHANGED"
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
rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"
echo ""
echo "✅ CHANGELOG written to $OUTPUT"
