#!/bin/bash
#
# generate-changelog.sh
# Generates a structured CHANGELOG.md from git commit history
#

set -e

REPO_PATH="${REPO_PATH:-.}"
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
FROM_TAG=""
INCLUDE_ALL=false

usage() {
    echo "Usage: $0 [--repo <path>] [--output <file>] [--from-tag <tag>] [--all]"
    echo ""
    echo "Options:"
    echo "  --repo <path>      Path to git repository (default: current directory)"
    echo "  --output <file>   Output file path (default: CHANGELOG.md)"
    echo "  --from-tag <tag>  Start from specific tag"
    echo "  --all             Include all commits (ignore tags)"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --from-tag)
            FROM_TAG="$2"
            shift 2
            ;;
        --all)
            INCLUDE_ALL=true
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Resolve repo path to absolute
REPO_PATH="$(cd "$REPO_PATH" && pwd)"

# Check if it's a git repo
if [[ ! -d "$REPO_PATH/.git" ]]; then
    echo "Error: Not a git repository: $REPO_PATH"
    exit 1
fi

cd "$REPO_PATH"

# Determine starting commit
if [[ "$INCLUDE_ALL" == true ]]; then
    START_COMMIT=""
    TAG_NAME="All Commits"
elif [[ -n "$FROM_TAG" ]]; then
    START_COMMIT="$FROM_TAG"
    TAG_NAME="$FROM_TAG"
elif START_COMMIT=$(git describe --tags --abbrev=0 2>/dev/null); then
    TAG_NAME="$START_COMMIT"
else
    # No tags found, use initial commit
    START_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null) || START_COMMIT="HEAD"
    TAG_NAME="Initial"
fi

# Get commits since tag (exclude the tag commit itself)
if [[ -z "$START_COMMIT" ]] || [[ "$START_COMMIT" == "All Commits" ]]; then
    COMMITS=$(git log --format='%s' 2>/dev/null)
else
    COMMITS=$(git log --format='%s' "$START_COMMIT"..HEAD 2>/dev/null)
fi

# Initialize category files using temp files
ADDED_FILE=$(mktemp)
FIXED_FILE=$(mktemp)
CHANGED_FILE=$(mktemp)
REMOVED_FILE=$(mktemp)
DOCS_FILE=$(mktemp)
PERF_FILE=$(mktemp)
TESTING_FILE=$(mktemp)
OTHER_FILE=$(mktemp)

cleanup() {
    rm -f "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE"
    rm -f "$DOCS_FILE" "$PERF_FILE" "$TESTING_FILE" "$OTHER_FILE"
}
trap cleanup EXIT

# Clean the commit message for display
clean_commit() {
    echo "$1" | sed 's/^feat://g' | sed 's/^add://g' | sed 's/^fix://g' | sed 's/^bugfix://g' \
        | sed 's/^chore://g' | sed 's/^refactor://g' | sed 's/^update://g' \
        | sed 's/^remove://g' | sed 's/^delete://g' | sed 's/^docs://g' \
        | sed 's/^perf://g' | sed 's/^optimize://g' | sed 's/^test://g' | xargs
}

# Categorize commits
categorize_commit() {
    local msg="$1"
    local lc_msg="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"
    local cleaned="$(clean_commit "$msg")"

    if echo "$lc_msg" | grep -qE '^(feat:|add:)'; then
        echo "- $cleaned" >> "$ADDED_FILE"
    elif echo "$lc_msg" | grep -qE '^(fix:|bugfix:)'; then
        echo "- $cleaned" >> "$FIXED_FILE"
    elif echo "$lc_msg" | grep -qE '^(remove:|delete:)'; then
        echo "- $cleaned" >> "$REMOVED_FILE"
    elif echo "$lc_msg" | grep -qE '^docs:'; then
        echo "- $cleaned" >> "$DOCS_FILE"
    elif echo "$lc_msg" | grep -qE '^(perf:|optimize:)'; then
        echo "- $cleaned" >> "$PERF_FILE"
    elif echo "$lc_msg" | grep -qE '^test:'; then
        echo "- $cleaned" >> "$TESTING_FILE"
    elif echo "$lc_msg" | grep -qE '^(chore:|refactor:|update:)'; then
        echo "- $cleaned" >> "$CHANGED_FILE"
    else
        echo "- $cleaned" >> "$OTHER_FILE"
    fi
}

# Process each commit
while IFS= read -r commit; do
    [[ -n "$commit" ]] && categorize_commit "$commit"
done <<< "$COMMITS"

# Read content from files
read_added() { cat "$ADDED_FILE" 2>/dev/null || true; }
read_fixed() { cat "$FIXED_FILE" 2>/dev/null || true; }
read_changed() { cat "$CHANGED_FILE" 2>/dev/null || true; }
read_removed() { cat "$REMOVED_FILE" 2>/dev/null || true; }
read_docs() { cat "$DOCS_FILE" 2>/dev/null || true; }
read_perf() { cat "$PERF_FILE" 2>/dev/null || true; }
read_testing() { cat "$TESTING_FILE" 2>/dev/null || true; }
read_other() { cat "$OTHER_FILE" 2>/dev/null || true; }

# Generate changelog
{
    echo "# Changelog"
    echo ""
    echo "## [$TAG_NAME]"
    echo ""
    
    if [[ -s "$ADDED_FILE" ]]; then
        echo "### Added"
        echo ""
        cat "$ADDED_FILE"
        echo ""
    fi
    
    if [[ -s "$FIXED_FILE" ]]; then
        echo "### Fixed"
        echo ""
        cat "$FIXED_FILE"
        echo ""
    fi
    
    if [[ -s "$CHANGED_FILE" ]]; then
        echo "### Changed"
        echo ""
        cat "$CHANGED_FILE"
        echo ""
    fi
    
    if [[ -s "$REMOVED_FILE" ]]; then
        echo "### Removed"
        echo ""
        cat "$REMOVED_FILE"
        echo ""
    fi
    
    if [[ -s "$DOCS_FILE" ]]; then
        echo "### Documentation"
        echo ""
        cat "$DOCS_FILE"
        echo ""
    fi
    
    if [[ -s "$PERF_FILE" ]]; then
        echo "### Performance"
        echo ""
        cat "$PERF_FILE"
        echo ""
    fi
    
    if [[ -s "$TESTING_FILE" ]]; then
        echo "### Testing"
        echo ""
        cat "$TESTING_FILE"
        echo ""
    fi
    
    if [[ -s "$OTHER_FILE" ]]; then
        echo "### Other"
        echo ""
        cat "$OTHER_FILE"
        echo ""
    fi
    
    echo "_Generated by changelog skill_"
} > "$OUTPUT_FILE"

echo "✓ CHANGELOG.md generated: $OUTPUT_FILE"
echo "  From tag: $TAG_NAME"

exit 0
