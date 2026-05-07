#!/bin/bash
# generate-changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [options]
# Options: --output FILE, --since TAG, --dry-run

set -e

# Defaults
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since|-s)
            SINCE_TAG="$2"
            shift 2
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: bash changelog.sh [options]"
            echo ""
            echo "Options:"
            echo "  --output, -o FILE   Output file path (default: CHANGELOG.md)"
            echo "  --since, -s TAG     Start from this tag (default: last git tag)"
            echo "  --dry-run, -n       Preview without writing file"
            echo "  --help, -h          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get the base commit (last tag or initial commit)
if [ -z "$SINCE_TAG" ]; then
    BASE_COMMIT=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$BASE_COMMIT" ]; then
        BASE_COMMIT=$(git rev-list --max-parents=0 HEAD)
        SINCE_TAG="Initial commit"
    else
        SINCE_TAG="$BASE_COMMIT"
    fi
fi

# Get current version (from last tag or default)
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "Unreleased")

# Fetch commits
COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short ${BASE_COMMIT}..HEAD 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No commits found since $SINCE_TAG"
    exit 0
fi

# Categorize commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a DOCS=()
declare -a TESTS=()
declare -a CHORE=()
declare -a OTHER=()

while IFS='|' read -r hash subject author date; do
    subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$subject_lower" =~ ^(feat|feature|add|new): ]]; then
        ADDED+=("- $subject")
    elif [[ "$subject_lower" =~ ^(fix|bugfix|patch|resolve): ]]; then
        FIXED+=("- $subject")
    elif [[ "$subject_lower" =~ ^(change|refactor|improve|update|optimize): ]]; then
        CHANGED+=("- $subject")
    elif [[ "$subject_lower" =~ ^(remove|delete|drop|deprecate): ]]; then
        REMOVED+=("- $subject")
    elif [[ "$subject_lower" =~ ^(docs|doc|readme): ]]; then
        DOCS+=("- $subject")
    elif [[ "$subject_lower" =~ ^test: ]]; then
        TESTS+=("- $subject")
    elif [[ "$subject_lower" =~ ^(chore|ci|build): ]]; then
        CHORE+=("- $subject")
    else
        OTHER+=("- $subject")
    fi
done <<< "$COMMITS"

# Generate changelog
generate_changelog() {
    local version="$1"
    local date=$(date +%Y-%m-%d)
    
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    
    # Unreleased section
    if [ "$version" = "Unreleased" ]; then
        echo "## [Unreleased]"
        echo ""
    else
        echo "## [$version] - $date"
        echo ""
    fi
    
    # Added
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Fixed
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Changed
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Removed
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Documentation
    if [ ${#DOCS[@]} -gt 0 ]; then
        echo "### Documentation"
        for item in "${DOCS[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Tests
    if [ ${#TESTS[@]} -gt 0 ]; then
        echo "### Tests"
        for item in "${TESTS[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Chore
    if [ ${#CHORE[@]} -gt 0 ]; then
        echo "### Chore"
        for item in "${CHORE[@]}"; do echo "$item"; done
        echo ""
    fi
    
    # Other
    if [ ${#OTHER[@]} -gt 0 ]; then
        echo "### Other"
        for item in "${OTHER[@]}"; do echo "$item"; done
        echo ""
    fi
}

# Output
CHANGELONG=$(generate_changelog "$CURRENT_VERSION")

if [ "$DRY_RUN" = true ]; then
    echo "$CHANGELONG"
else
    echo "$CHANGELONG" > "$OUTPUT_FILE"
    echo "✅ Changelog generated: $OUTPUT_FILE"
    echo "   Version: $CURRENT_VERSION"
    echo "   Commits: $(echo "$COMMITS" | wc -l)"
fi
