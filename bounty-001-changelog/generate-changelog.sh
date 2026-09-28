#!/usr/bin/env bash
# generate-changelog.sh — generate a structured CHANGELOG.md from git history.
# Usage:
#   ./generate-changelog.sh [repo-dir]       (default: current directory)
#
# Categorizes commits since the last git tag into Added/Fixed/Changed/Removed
# by message prefix, and prepends the new section to CHANGELOG.md.

set -euo pipefail
REPO="${1:-.}"
cd "$REPO"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo)"
if [ -z "$LAST_TAG" ]; then
  echo "No tags found. Falling back to current branch root." >&2
  RANGE="HEAD"
else
  RANGE="${LAST_TAG}..HEAD"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo "Collecting commits since: ${RANGE:-root} ..." >&2
log=$(git log --no-merges --pretty=format:'%s' "$RANGE")

# Categorize by conventional commit type (case-insensitive).
added=""; fixed=""; changed=""; removed=""; other=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  subject="$line"
  case "$(echo "$subject" | tr '[:upper:]' '[:lower:]')" in
    feat:*|feature:*|add:*|new:*|"*")
      msg="${subject#*:}"
      added="$added\n- ${msg# }" ;;
    fix:*|bugfix:*|bug:*|hotfix:*)
      msg="${subject#*:}"
      fixed="$fixed\n- ${msg# }" ;;
    refactor:*|perf:*|improve:*|rework:*|update:*|bump:*)
      msg="${subject#*:}"
      changed="$changed\n- ${msg# }" ;;
    remove:*|drop:*|delete:*|revert:*)
      msg="${subject#*:}"
      removed="$removed\n- ${msg# }" ;;
    *)
      msg="${subject#*:}"
      other="$other\n- ${msg# }" ;;
  esac
done <<< "$log"

VERSION="$(git describe --tags --abbrev=0 2>/dev/null || echo 'unreleased')"
DATE="$(date +%Y-%m-%d)"

{
  echo "# Changelog"
  echo ""
  echo "## $VERSION ($DATE)"
  echo ""
  [ -n "$added" ]   && echo "### Added" && echo -e "$added"   && echo ""
  [ -n "$fixed" ]   && echo "### Fixed" && echo -e "$fixed"   && echo ""
  [ -n "$changed" ] && echo "### Changed" && echo -e "$changed" && echo ""
  [ -n "$removed" ] && echo "### Removed" && echo -e "$removed" && echo ""
  [ -n "$other" ]   && echo "### Other" && echo -e "$other"   && echo ""
} > "$TMP"

# Prepend new section above any existing changelog entries.
if [ -f CHANGELOG.md ]; then
  sed -n '/^# Changelog$/,$p' CHANGELOG.md | tail -n +2 > "$TMP.tmp"
  mv "$TMP.tmp" "$TMP.tmp2"
  {
    cat "$TMP"
    cat "$TMP.tmp2"
  } > "$TMP.final"
  mv "$TMP.final" CHANGELOG.md
else
  cp "$TMP" CHANGELOG.md
fi
rm -f "$TMP.tmp" "$TMP.tmp2" "$TMP.final"

echo "Wrote CHANGELOG.md"
head -20 CHANGELOG.md