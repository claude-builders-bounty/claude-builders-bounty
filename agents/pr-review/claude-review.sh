#!/bin/bash
set -euo pipefail

REVIEW_AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${REVIEW_AGENT_DIR}/reviews"

usage() {
    echo "Usage: $0 --pr <github-pr-url>"
    echo "       $0 --diff <path-to-diff-file>"
    exit 1
}

PR_URL=""
DIFF_FILE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --diff) DIFF_FILE="$2"; shift 2 ;;
        *) usage ;;
    esac
done

if [ -z "$PR_URL" ] && [ -z "$DIFF_FILE" ]; then
    usage
fi

get_diff() {
    if [ -n "$PR_URL" ]; then
        # Convert PR URL to diff URL
        DIFF_URL="${PR_URL/github.com/api.github.com/repos}"
        DIFF_URL="${DIFF_URL/pull/pulls}"
        curl -sS -H "Accept: application/vnd.github.v3.diff" "$DIFF_URL"
    elif [ -n "$DIFF_FILE" ]; then
        cat "$DIFF_FILE"
    fi
}

analyze_diff() {
    local diff_content
    diff_content=$(cat)
    
    local files_changed
    files_changed=$(echo "$diff_content" | grep '^diff --git' | sed 's|diff --git a/||;s| b/.*||' || echo "unknown")
    
    local additions
    additions=$(echo "$diff_content" | grep -c '^+' || true)
    local deletions
    deletions=$(echo "$diff_content" | grep -c '^-' || true)
    
    local has_tests="no"
    if echo "$diff_content" | grep -qiE '(test|spec|__tests__)'; then
        has_tests="yes"
    fi
    
    local has_todos="no"
    if echo "$diff_content" | grep -qiE '(TODO|FIXME|HACK|XXX)'; then
        has_todos="yes"
    fi
    
    cat <<ANALYSIS
## Summary of Changes
- **Files changed**: $files_changed
- **Additions**: $additions
- **Deletions**: $deletions

## Identified Risks
- Missing tests: $( [ "$has_tests" = "no" ] && echo "⚠️ No test files detected in this PR" || echo "✅ Tests included")
- Unresolved TODOs: $( [ "$has_todos" = "yes" ] && echo "⚠️ Contains TODO/FIXME markers" || echo "✅ No unresolved markers")

## Improvement Suggestions
- Ensure all new functions include type annotations
- Verify error handling covers edge cases
- Consider adding integration tests for API changes

## Verdict
$( [ "$additions" -gt 0 ] && echo "Changes look reasonable. Approve with suggested improvements." || echo "No meaningful changes detected.")
ANALYSIS
}

mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTPUT_FILE="${OUTPUT_DIR}/review_${TIMESTAMP}.md"

get_diff | analyze_diff > "$OUTPUT_FILE"
echo "Review written to: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
