#!/bin/bash

# generate-changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh
#    or: /generate-changelog (if used as a Claude Code skill)

set -e

OUTPUT_FILE="CHANGELOG.md"
TEMP_FILE=$(mktemp)

# Get the last git tag (or use root commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    # No tags — use all commits
    COMMITS=$(git log --pretty=format:"%s|%an|%ad" --date=short)
    RANGE="all commits"
else
    COMMITS=$(git log "${LAST_TAG}..HEAD" --pretty=format:"%s|%an|%ad" --date=short)
    RANGE="since ${LAST_TAG}"
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Parse commits into categories
while IFS='|' read -r msg author date; do
    [ -z "$msg" ] && continue
    
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    case "$lower_msg" in
        feat:*|add*|new*|create*|implement*|introduce*)
            ADDED="${ADDED}\n- ${msg} (${author}, ${date})"
            ;;
        fix:*|bug*|hotfix*|patch*|resolve*|correct*)
            FIXED="${FIXED}\n- ${msg} (${author}, ${date})"
            ;;
        change:*|update*|refactor*|improve*|optimize*|modify*)
            CHANGED="${CHANGED}\n- ${msg} (${author}, ${date})"
            ;;
        remove:*|delete*|drop*|deprecate*)
            REMOVED="${REMOVED}\n- ${msg} (${author}, ${date})"
            ;;
        *)
            # Default to Changed for uncategorized commits
            CHANGED="${CHANGED}\n- ${msg} (${author}, ${date})"
            ;;
    esac
done <<< "$COMMITS"

# Get current date and version
TODAY=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")

# Build the changelog
cat > "$TEMP_FILE" << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

HEADER

echo "## [${VERSION}] - ${TODAY}" >> "$TEMP_FILE"
echo "" >> "$TEMP_FILE"

if [ -n "$ADDED" ]; then
    echo "### Added" >> "$TEMP_FILE"
    echo -e "$ADDED" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$TEMP_FILE"
    echo -e "$FIXED" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$TEMP_FILE"
    echo -e "$CHANGED" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$TEMP_FILE"
    echo -e "$REMOVED" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

# If no changes found
if [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ]; then
    echo "### Changed" >> "$TEMP_FILE"
    echo "- No notable changes" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

# Prepend to existing CHANGELOG or create new one
if [ -f "$OUTPUT_FILE" ]; then
    # Keep existing content after the header
    EXISTING=$(tail -n +8 "$OUTPUT_FILE" 2>/dev/null || true)
    if [ -n "$EXISTING" ]; then
        cat "$TEMP_FILE" > "${OUTPUT_FILE}.new"
        echo "" >> "${OUTPUT_FILE}.new"
        echo "$EXISTING" >> "${OUTPUT_FILE}.new"
        mv "${OUTPUT_FILE}.new" "$OUTPUT_FILE"
    else
        mv "$TEMP_FILE" "$OUTPUT_FILE"
    fi
else
    mv "$TEMP_FILE" "$OUTPUT_FILE"
fi

echo "✅ Generated ${OUTPUT_FILE} with changes ${RANGE}"
echo ""
cat "$OUTPUT_FILE"
