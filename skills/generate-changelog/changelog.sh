#!/usr/bin/env bash
# CHANGELOG Generator — Bounty #1 ($50)
# Generates structured CHANGELOG.md from git history with auto-categorization.

set -eo pipefail

OUTPUT="CHANGELOG.md"
TAG_PATTERN="v*"

# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 --match "$TAG_PATTERN" 2>/dev/null || true)

if [ -n "$LATEST_TAG" ]; then
  RANGE="$LATEST_TAG..HEAD"
else
  RANGE=""
fi

# Get commits
git log --pretty=format:"%s" $RANGE > /tmp/commits.txt

if [ ! -s /tmp/commits.txt ]; then
  echo "No new commits since last tag."
  exit 0
fi

# Build sections
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
  [ -z "$msg" ] && continue
  low=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  case "$low" in
    add*|feat*|new*|introduce*|implement*|create*|support*)
      ADDED="${ADDED}- $msg\n"
      ;;
    fix*|bug*|hotfix*|patch*|correct*|resolve*|repair*)
      FIXED="${FIXED}- $msg\n"
      ;;
    remove*|delete*|drop*|discard*|eliminate*|deprecate*)
      REMOVED="${REMOVED}- $msg\n"
      ;;
    *)
      CHANGED="${CHANGED}- $msg\n"
      ;;
  esac
done < /tmp/commits.txt

# Remove trailing newlines
ADDED=$(echo -n "$ADDED")
FIXED=$(echo -n "$FIXED")
CHANGED=$(echo -n "$CHANGED")
REMOVED=$(echo -n "$REMOVED")

# Generate output
cat > "$OUTPUT" <<EOF
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

EOF

[ -n "$ADDED" ] && cat >> "$OUTPUT" <<EOF
### Added
$ADDED
EOF

[ -n "$FIXED" ] && cat >> "$OUTPUT" <<EOF
### Fixed
$FIXED
EOF

[ -n "$CHANGED" ] && cat >> "$OUTPUT" <<EOF
### Changed
$CHANGED
EOF

[ -n "$REMOVED" ] && cat >> "$OUTPUT" <<EOF
### Removed
$REMOVED
EOF

# If no categories matched, show other section
if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
  cat >> "$OUTPUT" <<EOF
### Other
$OTHER
EOF
fi

total=$(wc -l < /tmp/commits.txt)
echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "Total commits: $total" >> "$OUTPUT"

echo "✓ Generated $OUTPUT ($total commits from $RANGE)"
