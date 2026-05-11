#!/usr/bin/env bash
# generate-changelog.sh — Auto-generate structured CHANGELOG.md from git history
# Bounty: claude-builders-bounty#1 ($50)
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_PATH="${2:-.}"

cd "$REPO_PATH"

# ── Get the last tag ──────────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
  echo "⚠️  No git tags found. Using the first commit as starting point."
  LAST_TAG=$(git rev-list --max-parents=0 HEAD)
  FROM_REF="$LAST_TAG"
else
  FROM_REF="$LAST_TAG"
fi

echo "📋 Generating changelog from $FROM_REF to HEAD..."

# ── Collect commits ───────────────────────────────────────────
COMMITS=$(git log "$FROM_REF..HEAD" --no-merges --pretty=format:'%s' 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
  echo "❌ No new commits since $FROM_REF."
  exit 0
fi

# ── Categorize commits ────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  msg=$(echo "$line" | sed 's/^[^a-zA-Z]*//')  # strip non-alpha prefix

  if echo "$msg" | grep -qiE '^(feat|add|new|implement|create|introduce)'; then
    ADDED+=("$msg")
  elif echo "$msg" | grep -qiE '^(fix|bug|patch|resolve|hotfix|correct)'; then
    FIXED+=("$msg")
  elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|kill)'; then
    REMOVED+=("$msg")
  else
    CHANGED+=("$msg")
  fi
done <<< "$COMMITS"

# ── Get version and date ──────────────────────────────────────
VERSION="${LAST_TAG:-0.0.0}"
DATE=$(date +%Y-%m-%d)
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

# ── Write CHANGELOG.md ────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION → HEAD] — $DATE"
  echo ""
  echo "> $TOTAL commits since \`$FROM_REF\`"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for item in "${ADDED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for item in "${FIXED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for item in "${CHANGED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for item in "${REMOVED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "✅ Changelog written to $OUTPUT_FILE ($TOTAL commits in 4 categories)"
echo ""
head -20 "$OUTPUT_FILE"
