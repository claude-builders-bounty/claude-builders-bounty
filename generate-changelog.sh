#!/usr/bin/env bash
# generate-changelog.sh - Generate structured CHANGELOG from git history
# Usage: ./generate-changelog.sh [output_file]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//' || echo "")
REPO_NAME=$(basename "$REPO_URL" 2>/dev/null || basename "$(pwd)")

# Get the last tag, or use empty if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Determine commit range
if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    VERSION="${LAST_TAG} → HEAD"
else
    COMMIT_RANGE="HEAD"
    VERSION="Unreleased"
fi

# Colors for terminal output (if interactive)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

echo -e "${GREEN}Generating CHANGELOG for $REPO_NAME...${NC}"
echo -e "${YELLOW}Version: $VERSION${NC}"

# Function to categorize commits
categorize_commits() {
    local pattern="$1"
    git log "$COMMIT_RANGE" --pretty=format:"%s" --reverse 2>/dev/null | grep -iE "$pattern" || true
}

# Extract commits by category
ADDED=$(categorize_commits "^(feat|add|implement|new|introduce)")
FIXED=$(categorize_commits "^(fix|bug|repair|correct|resolve|hotfix)")
CHANGED=$(categorize_commits "^(change|update|modify|refactor|improve|enhance|optimize|upgrade)")
REMOVED=$(categorize_commits "^(remove|delete|drop|deprecate|clean)")
DOCS=$(categorize_commits "^(doc|readme|comment|guide)")
TESTS=$(categorize_commits "^(test|spec|coverage)")
SECURITY=$(categorize_commits "^(security|vuln|cve|auth|protect)")

# Format commit line
format_commit() {
    local line="$1"
    # Extract PR number if present (#123)
    local pr=$(echo "$line" | grep -oE '#[0-9]+' | head -1 || true)
    # Clean up the message
    local msg=$(echo "$line" | sed -E 's/^(feat|fix|add|update|change|remove|doc|test|security)(\([^)]+\))?:?\s*//i' | sed 's/^[[:space:]]*//')
    
    if [ -n "$pr" ] && [ -n "$REPO_URL" ]; then
        echo "- $msg [$pr]($REPO_URL/pull/${pr#\#})"
    else
        echo "- $msg"
    fi
}

# Generate category section
generate_section() {
    local title="$1"
    local commits="$2"
    
    if [ -n "$commits" ]; then
        echo "### $title"
        echo ""
        echo "$commits" | while IFS= read -r line; do
            [ -n "$line" ] && format_commit "$line"
        done
        echo ""
    fi
}

# Generate the CHANGELOG
cat > "$OUTPUT_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$(date +%Y-%m-%d)]

EOF

# Append each section
generate_section "🚀 Added" "$ADDED" >> "$OUTPUT_FILE"
generate_section "🐛 Fixed" "$FIXED" >> "$OUTPUT_FILE"
generate_section "🔧 Changed" "$CHANGED" >> "$OUTPUT_FILE"
generate_section "🗑️ Removed" "$REMOVED" >> "$OUTPUT_FILE"
generate_section "📚 Documentation" "$DOCS" >> "$OUTPUT_FILE"
generate_section "🧪 Tests" "$TESTS" >> "$OUTPUT_FILE"
generate_section "🔒 Security" "$SECURITY" >> "$OUTPUT_FILE"

# Add compare link if we have a tag and repo URL
if [ -n "$LAST_TAG" ] && [ -n "$REPO_URL" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "[Full Changelog]($REPO_URL/compare/$LAST_TAG...HEAD)" >> "$OUTPUT_FILE"
fi

echo -e "${GREEN}✅ CHANGELOG generated: $OUTPUT_FILE${NC}"

# Show preview
if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${YELLOW}Preview (first 50 lines):${NC}"
    head -50 "$OUTPUT_FILE"
    echo ""
    echo -e "${GREEN}Total lines: $(wc -l < "$OUTPUT_FILE")${NC}"
fi
