#!/bin/bash
# Changelog generator: creates CHANGELOG.md from git history since last tag
# Usage: bash changelog.sh or /generate-changelog (via Claude Code SKILL)

set -e

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    # No tags yet, use all commits
    COMMIT_RANGE=""
    echo "No tags found, using all commits."
else
    COMMIT_RANGE="$LAST_TAG..HEAD"
    echo "Generating changelog since tag: $LAST_TAG"
fi

# Temporary file
TMP_FILE=$(mktemp)

# Header
cat > CHANGELOG.md <<EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF

# Get commits and categorize
git log $COMMIT_RANGE --pretty=format:"%s" --no-merges | while read -r line; do
    # Categorize based on conventional commit prefixes
    if [[ "$line" =~ ^feat.*: ]] || [[ "$line" =~ ^add.*: ]] || [[ "$line" =~ ^new.*: ]]; then
        echo "## Added" >> "$TMP_FILE"
        echo "- $line" >> "$TMP_FILE"
    elif [[ "$line" =~ ^fix.*: ]] || [[ "$line" =~ ^bug.*: ]] || [[ "$line" =~ ^patch.*: ]]; then
        echo "## Fixed" >> "$TMP_FILE"
        echo "- $line" >> "$TMP_FILE"
    elif [[ "$line" =~ ^change.*: ]] || [[ "$line" =~ ^update.*: ]] || [[ "$line" =~ ^modify.*: ]]; then
        echo "## Changed" >> "$TMP_FILE"
        echo "- $line" >> "$TMP_FILE"
    elif [[ "$line" =~ ^remov.*: ]] || [[ "$line" =~ ^delete.*: ]]; then
        echo "## Removed" >> "$TMP_FILE"
        echo "- $line" >> "$TMP_FILE"
    else
        # Default to Changed for unlabeled commits
        echo "## Changed" >> "$TMP_FILE"
        echo "- $line" >> "$TMP_FILE"
    fi
done

# Remove duplicate headers and format
awk '!seen[$0]++ || !/^## /' "$TMP_FILE" >> CHANGELOG.md

rm -f "$TMP_FILE"

echo "✅ CHANGELOG.md generated successfully!"
echo "📄 File: $(pwd)/CHANGELOG.md"
