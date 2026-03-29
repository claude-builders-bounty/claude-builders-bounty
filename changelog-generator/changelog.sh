#!/bin/bash
# changelog.sh - Generate CHANGELOG from git history

OUTPUT="${1:-CHANGELOG.md}"
SINCE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD~20')}"

echo "Generating CHANGELOG from $SINCE to HEAD..."

{
  echo "# CHANGELOG"
  echo ""
  echo "## [Unreleased] - $(date +%Y-%m-%d)"
  echo ""

  # Added
  echo "### Added"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="feat\|add\|new" -i | sort -u
  echo ""
  echo ""

  # Changed
  echo "### Changed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="change\|update\|modify\|refactor" -i | sort -u
  echo ""
  echo ""

  # Fixed
  echo "### Fixed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="fix\|bug\|patch" -i | sort -u
  echo ""
  echo ""

  # Removed
  echo "### Removed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="remove\|delete\|deprecate" -i | sort -u
  echo ""
  echo ""

  # Security
  echo "### Security"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="security\|vuln\|cve" -i | sort -u
  echo ""
  echo ""

  # Performance
  echo "### Performance"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="perf\|optimize\|speed" -i | sort -u
  echo ""

} > "$OUTPUT"

echo "✅ CHANGELOG generated: $OUTPUT"
