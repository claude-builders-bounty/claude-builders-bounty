#!/usr/bin/env bash
# generate-changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [range] [output-file]
# Example: bash generate-changelog.sh v1.0.0..HEAD CHANGELOG.md

set -euo pipefail

RANGE="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"

if [[ -z "$RANGE" ]]; then
    # Find last tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$LAST_TAG" ]]; then
        RANGE="HEAD"
    else
        RANGE="${LAST_TAG}..HEAD"
    fi
fi

# Get commits
COMMITS=$(git log "$RANGE" --pretty=format:"%h %s (%an, %ad)" --date=short)

if [[ -z "$COMMITS" ]]; then
    echo "No commits found in range: $RANGE"
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    # Extract subject (after hash)
    SUBJECT=$(echo "$line" | sed 's/^[0-9a-f]\{7\} //')
    
    # Categorize by prefix
    if [[ "$SUBJECT" =~ ^[Aa]dd(?:ed)?[:\ ]+(.*) ]]; then
        ADDED+="- ${BASH_REMATCH[1]}\n"
    elif [[ "$SUBJECT" =~ ^[Ff]ix(?:ed)?[:\ ]+(.*) ]]; then
        FIXED+="- ${BASH_REMATCH[1]}\n"
    elif [[ "$SUBJECT" =~ ^[Cc]hange(?:d)?[:\ ]+(.*) ]]; then
        CHANGED+="- ${BASH_REMATCH[1]}\n"
    elif [[ "$SUBJECT" =~ ^[Rr]emove(?:d)?[:\ ]+(.*) ]]; then
        REMOVED+="- ${BASH_REMATCH[1]}\n"
    else
        # Default to Changed
        CHANGED+="- ${SUBJECT}\n"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
cat > "$OUTPUT" << EOF
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
${ADDED:-No additions}

### Fixed
${FIXED:-No fixes}

### Changed
${CHANGED:-No changes}

### Removed
${REMOVED:-No removals}

EOF

echo "Changelog generated: $OUTPUT"
echo "Commits analyzed: $(echo "$COMMITS" | wc -l)"
