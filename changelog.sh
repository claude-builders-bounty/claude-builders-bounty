#!/usr/bin/env bash
# ==============================================================================
# changelog.sh - Fast structured git changelog generator
# Complies with Keep a Changelog & Conventional Commits.
# ==============================================================================

set -e

REPO_DIR="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

# Prefer python generator if available for full markdown parsing
if command -v python3 &>/dev/null; then
    python3 "$(dirname "$0")/scripts/generate_changelog.py" --repo "$REPO_DIR" --output "$OUTPUT_FILE"
    exit 0
elif command -v python &>/dev/null; then
    python "$(dirname "$0")/scripts/generate_changelog.py" --repo "$REPO_DIR" --output "$OUTPUT_FILE"
    exit 0
fi

# Pure bash fallback when python is not installed
LAST_TAG=$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || echo "")
TODAY=$(date +%Y-%m-%d)

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    SUB_HEADER="> *Changes since \`${LAST_TAG}\`*"
else
    RANGE="HEAD"
    SUB_HEADER="> *Initial release or all commits*"
fi

TMP_FILE=$(mktemp)

cat << 'EOF' > "$TMP_FILE"
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF

echo "## [Unreleased] - ${TODAY}" >> "$TMP_FILE"
echo "$SUB_HEADER" >> "$TMP_FILE"
echo "" >> "$TMP_FILE"

# Collect commits by category
ADDED=$(git -C "$REPO_DIR" log "$RANGE" --pretty=format:"- %s ([%h])" --grep="^feat" --grep="^add" -i || true)
FIXED=$(git -C "$REPO_DIR" log "$RANGE" --pretty=format:"- %s ([%h])" --grep="^fix" --grep="^bug" -i || true)
CHANGED=$(git -C "$REPO_DIR" log "$RANGE" --pretty=format:"- %s ([%h])" --grep="^refactor" --grep="^perf" --grep="^chore" --grep="^docs" -i || true)
REMOVED=$(git -C "$REPO_DIR" log "$RANGE" --pretty=format:"- %s ([%h])" --grep="^remove" --grep="^deprecat" --grep="^revert" -i || true)

if [ -n "$ADDED" ]; then
    echo "### Added" >> "$TMP_FILE"
    echo "$ADDED" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$TMP_FILE"
    echo "$FIXED" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$TMP_FILE"
    echo "$CHANGED" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$TMP_FILE"
    echo "$REMOVED" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
fi

mv "$TMP_FILE" "$OUTPUT_FILE"
echo "Successfully generated changelog at: $OUTPUT_FILE"
