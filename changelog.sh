#!/bin/bash
#
# changelog.sh - Generate structured CHANGELOG.md from git history
# Works with conventional commits (feat:, fix:, etc.) and fallback parsing
#

set -euo pipefail

# Configuration
DATE=$(date +%Y-%m-%d)
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

# Fetch the last tag or use empty string for all commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LAST_TAG" ]]; then
    COMMITS=$(git log "${LAST_TAG}"..HEAD --pretty=format:"%s" 2>/dev/null || true)
else
    # No tags exist, get all commits
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || true)
fi

# Initialize arrays as regular indexed arrays (not associative)
added=()
fixed=()
changed=()
removed=()

# Process commits (one per line)
while IFS= read -r subject; do
    # Skip empty commits
    [[ -z "$subject" ]] && continue
    
    # Normalize subject
    subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    # Categorize based on conventional commit prefixes
    if [[ "$subject_lower" =~ ^feat: || "$subject_lower" =~ ^feature: || "$subject_lower" =~ ^add: || "$subject_lower" =~ ^added: ]]; then
        added+=("$subject")
    elif [[ "$subject_lower" =~ ^fix: || "$subject_lower" =~ ^bugfix: || "$subject_lower" =~ ^bug: || "$subject_lower" =~ ^hotfix: ]]; then
        fixed+=("$subject")
    elif [[ "$subject_lower" =~ ^remove: || "$subject_lower" =~ ^removed: || "$subject_lower" =~ ^delete: || "$subject_lower" =~ ^deleted: ]]; then
        removed+=("$subject")
    else
        changed+=("$subject")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] - $DATE"
    echo ""
    
    if [[ ${#added[@]} -gt 0 ]]; then
        echo "### Added"
        for commit in "${added[@]}"; do
            # Strip the prefix and format
            clean=$(echo "$commit" | sed -E 's/^(feat|feature|add|added):[[:space:]]*/- /i')
            echo "  $clean"
        done
        echo ""
    fi
    
    if [[ ${#fixed[@]} -gt 0 ]]; then
        echo "### Fixed"
        for commit in "${fixed[@]}"; do
            clean=$(echo "$commit" | sed -E 's/^(fix|bugfix|bug|hotfix):[[:space:]]*/- /i')
            echo "  $clean"
        done
        echo ""
    fi
    
    if [[ ${#changed[@]} -gt 0 ]]; then
        echo "### Changed"
        for commit in "${changed[@]}"; do
            clean=$(echo "$commit" | sed 's/^/- /')
            echo "  $clean"
        done
        echo ""
    fi
    
    if [[ ${#removed[@]} -gt 0 ]]; then
        echo "### Removed"
        for commit in "${removed[@]}"; do
            clean=$(echo "$commit" | sed -E 's/^(remove|removed|delete|deleted):[[:space:]]*/- /i')
            echo "  $clean"
        done
        echo ""
    fi
    
    # If no commits found
    if [[ ${#added[@]} -eq 0 && ${#fixed[@]} -eq 0 && ${#changed[@]} -eq 0 && ${#removed[@]} -eq 0 ]]; then
        echo "No significant changes since last release."
        echo ""
    fi
    
} > "$OUTPUT_FILE"

echo "✅ Generated $OUTPUT_FILE"