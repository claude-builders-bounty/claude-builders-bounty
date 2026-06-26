#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate CHANGELOG.md from git history since last tag
# Usage: bash changelog.sh

TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${TAG:+$TAG..HEAD}"

if [ -z "$RANGE" ]; then
  RANGE="HEAD"
fi

# Build categories
ADDED=$(git log "$RANGE" --grep="^feat" --oneline --format="  - %s" 2>/dev/null || true)
FIXED=$(git log "$RANGE" --grep="^fix" --oneline --format="  - %s" 2>/dev/null || true)
CHANGED=$(git log "$RANGE" --grep="^refactor\|^perf\|^style" --oneline --format="  - %s" 2>/dev/null || true)
REMOVED=$(git log "$RANGE" --grep="^remove\|^chore" --oneline --format="  - %s" 2>/dev/null || true)
OTHER=$(git log "$RANGE" --oneline --format="  - %s" 2>/dev/null | head -5 || true)

DATE=$(date +%Y-%m-%d)
VERSION="${TAG:-v0.0.0}"

cat > CHANGELOG.md <<EOF
# Changelog

## $VERSION ($DATE)

EOF

[ -n "$ADDED" ]   && { echo -e "\n### Added\n$ADDED" >> CHANGELOG.md; }
[ -n "$FIXED" ]   && { echo -e "\n### Fixed\n$FIXED" >> CHANGELOG.md; }
[ -n "$CHANGED" ] && { echo -e "\n### Changed\n$CHANGED" >> CHANGELOG.md; }
[ -n "$REMOVED" ] && { echo -e "\n### Removed\n$REMOVED" >> CHANGELOG.md; }

wc -l CHANGELOG.md | awk '{print "✨ Generated", $1, "line changelog"}'
