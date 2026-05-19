#!/bin/bash
# =============================================================================
# generate-changelog.sh - Generate structured CHANGELOG.md from git history
# =============================================================================
# Usage: ./scripts/generate-changelog.sh
#
# This script automatically generates a structured CHANGELOG.md file following
# the "Keep a Changelog" format (https://keepachangelog.com/).
#
# Features:
# - Fetches commits since the last git tag
# - Auto-categorizes commits into: Added, Changed, Fixed, Removed
# - Outputs properly formatted CHANGELOG.md
# =============================================================================

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not a git repository."
    exit 1
fi

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    echo "Found tag: $LAST_TAG"
    COMMITS=$(git log --pretty=format:"%s" ${LAST_TAG}..HEAD 2>/dev/null)
else
    echo "No tags found, using all commits"
    COMMITS=$(git log --pretty=format:"%s")
fi

# Initialize sections
ADDED=""
CHANGED=""
FIXED=""
REMOVED=""

# Process each commit
while IFS= read -r line; do
    [ -z "$line" ] && continue

    msg_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

    # Categorize based on commit message keywords
    if echo "$msg_lower" | grep -qE "^(feat|add|new|creat|implement)|\badd\b|\bcreate\b|\bnew\b"; then
        ADDED="${ADDED}- ${line}"$'\n'
    elif echo "$msg_lower" | grep -qE "^(fix|patch|resolv)|\bfix\b|\bpatch\b|\bbugfix\b"; then
        FIXED="${FIXED}- ${line}"$'\n'
    elif echo "$msg_lower" | grep -qE "^(remov|delet|drop|deprec)|\bremov\b|\bdelet\b|\bdrop\b"; then
        REMOVED="${REMOVED}- ${line}"$'\n'
    else
        CHANGED="${CHANGED}- ${line}"$'\n'
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
cat > "$OUTPUT_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - $(date -u +%Y-%m-%d)

### Added
${ADDED}
### Changed
${CHANGED}
### Fixed
${FIXED}
### Removed
${REMOVED}
EOF

echo "Generated $OUTPUT_FILE"
