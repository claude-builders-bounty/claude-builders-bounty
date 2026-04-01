#!/usr/bin/env bash
# claude-review — Review a GitHub PR and output structured Markdown
# Usage: bash claude-review.sh --pr https://github.com/owner/repo/pull/123
# or: bash claude-review.sh --diff file.diff

set -euo pipefail

PR_URL=""
DIFF_FILE=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --diff) DIFF_FILE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: bash claude-review.sh --pr <PR_URL> [--output FILE]"
            echo "       bash claude-review.sh --diff <DIFF_FILE> [--output FILE]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Get the diff
if [[ -n "$PR_URL" ]]; then
    # Extract owner/repo/number from URL
    if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        PR_NUM="${BASH_REMATCH[3]}"
    else
        echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123"
        exit 1
    fi
    
    echo "📋 Fetching PR #$PR_NUM from $OWNER/$REPO..."
    
    # Get PR info
    PR_INFO=$(curl -sL "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM" \
        -H "Accept: application/vnd.github.v3+json" \
        ${GITHUB_TOKEN:+-H "Authorization: token $GITHUB_TOKEN"})
    
    PR_TITLE=$(echo "$PR_INFO" | jq -r '.title // "Unknown"')
    PR_BODY=$(echo "$PR_INFO" | jq -r '.body // "No description"' | head -20)
    PR_AUTHOR=$(echo "$PR_INFO" | jq -r '.user.login // "Unknown"')
    PR_FILES=$(echo "$PR_INFO" | jq -r '.changed_files // 0')
    PR_ADDITIONS=$(echo "$PR_INFO" | jq -r '.additions // 0')
    PR_DELETIONS=$(echo "$PR_INFO" | jq -r '.deletions // 0')
    
    # Get the diff
    DIFF=$(curl -sL "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM" \
        -H "Accept: application/vnd.github.v3.diff" \
        ${GITHUB_TOKEN:+-H "Authorization: token $GITHUB_TOKEN"})
    
    # Get changed files
    FILES_JSON=$(curl -sL "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM/files" \
        -H "Accept: application/vnd.github.v3+json" \
        ${GITHUB_TOKEN:+-H "Authorization: token $GITHUB_TOKEN"})
    
elif [[ -n "$DIFF_FILE" ]]; then
    if [[ ! -f "$DIFF_FILE" ]]; then
        echo "Error: Diff file not found: $DIFF_FILE"
        exit 1
    fi
    DIFF=$(cat "$DIFF_FILE")
    PR_TITLE="Local diff"
    PR_BODY=""
    PR_AUTHOR="local"
    PR_FILES=$(echo "$DIFF" | grep -c "^diff --git" || true)
    PR_ADDITIONS=$(echo "$DIFF" | grep -c "^+" || true)
    PR_DELETIONS=$(echo "$DIFF" | grep -c "^-" || true)
else
    echo "Error: Provide --pr <URL> or --diff <FILE>"
    exit 1
fi

# Truncate diff if too large (for Claude API)
DIFF_SIZE=${#DIFF}
if [[ $DIFF_SIZE -gt 50000 ]]; then
    echo "⚠️  Diff is large ($DIFF_SIZE chars). Truncating to 50,000 chars."
    DIFF="${DIFF:0:50000}"
fi

echo "📝 Analyzing $PR_FILES files (+$PR_ADDITIONS/-$PR_DELETIONS)..."

# Analyze the diff
# Extract changed files and their diffs
REVIEW=""

# Count patterns
BUGS=0
SECURITY=0
STYLE=0
PERF=0

# Check for common issues in the diff
check_pattern() {
    local pattern="$1"
    local category="$2"
    local message="$3"
    local matches
    matches=$(echo "$DIFF" | grep -n "$pattern" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
        REVIEW="$REVIEW\n- **[$category]** $message"
        case "$category" in
            Bug) ((BUGS++)) || true ;;
            Security) ((SECURITY++)) || true ;;
            Performance) ((PERF++)) || true ;;
            Style) ((STYLE++)) || true ;;
        esac
    fi
}

# Security checks
check_pattern "password.*=.*['\"]" "Security" "Hardcoded password detected"
check_pattern "api[_-]?key.*=.*['\"]" "Security" "Hardcoded API key detected"
check_pattern "TODO.*hack\|FIXME.*security\|XXX" "Security" "Security-related TODO/FIXME found"
check_pattern "eval(" "Security" "Use of eval() detected — potential code injection risk"
check_pattern "innerHTML" "Security" "Direct innerHTML usage — potential XSS vulnerability"
check_pattern "dangerouslySetInnerHTML" "Security" "dangerouslySetInnerHTML usage — ensure input is sanitized"
check_pattern "exec(" "Security" "Use of exec() — potential command injection"
check_pattern "SELECT.*\*.*FROM" "Security" "SELECT * query — consider specifying columns"

# Bug risk checks
check_pattern "catch.*{}" "Bug" "Empty catch block — errors will be silently swallowed"
check_pattern "console\.log" "Bug" "console.log left in code — consider removing for production"
check_pattern "debugger" "Bug" "debugger statement left in code"
check_pattern "\.then(.*=>.*{" "Bug" "Nested promise chain — consider using async/await"
check_pattern "==\s" "Bug" "Loose equality (==) used — prefer strict equality (===)"

# Performance checks  
check_pattern "useEffect.*\[\]" "Performance" "useEffect with empty deps — verify this only needs to run once"
check_pattern "new Date()" "Performance" "new Date() in render — may cause unnecessary re-renders"
check_pattern "JSON\.parse.*JSON\.stringify" "Performance" "JSON parse+stringify for deep clone — consider structuredClone()"

# Generate the summary
TOTAL_ISSUES=$((BUGS + SECURITY + STYLE + PERF))

# Determine the changed file list
CHANGED_FILES=""
if [[ -n "${FILES_JSON:-}" ]]; then
    CHANGED_FILES=$(echo "$FILES_JSON" | jq -r '.[].filename' 2>/dev/null || echo "")
fi
if [[ -z "$CHANGED_FILES" ]]; then
    CHANGED_FILES=$(echo "$DIFF" | grep "^diff --git" | sed 's/diff --git a\///' | sed 's/ b\/.*//')
fi

# Build the review markdown
{
    echo "# PR Review: $PR_TITLE"
    echo ""
    echo "**Author:** $PR_AUTHOR | **Files:** $PR_FILES | **Changes:** +$PR_ADDITIONS/-$PR_DELETIONS"
    echo ""
    echo "---"
    echo ""
    echo "## Summary"
    echo ""
    echo "This PR modifies $PR_FILES file(s) with $PR_ADDITIONS additions and $PR_DELETIONS deletions."
    if [[ -n "$PR_BODY" && "$PR_BODY" != "No description" ]]; then
        echo ""
        echo "> $(echo "$PR_BODY" | head -3)"
    fi
    echo ""
    echo "## Changed Files"
    echo ""
    echo "$CHANGED_FILES" | while read -r f; do
        [[ -n "$f" ]] && echo "- \`$f\`"
    done
    echo ""
    
    if [[ $TOTAL_ISSUES -gt 0 ]]; then
        echo "## Identified Risks ($TOTAL_ISSUES)"
        echo ""
        if [[ $SECURITY -gt 0 ]]; then
            echo "### 🔒 Security ($SECURITY)"
            echo -e "$REVIEW" | grep "\[Security\]"
            echo ""
        fi
        if [[ $BUGS -gt 0 ]]; then
            echo "### 🐛 Bugs ($BUGS)"
            echo -e "$REVIEW" | grep "\[Bug\]"
            echo ""
        fi
        if [[ $PERF -gt 0 ]]; then
            echo "### ⚡ Performance ($PERF)"
            echo -e "$REVIEW" | grep "\[Performance\]"
            echo ""
        fi
    else
        echo "## Identified Risks"
        echo ""
        echo "✅ No obvious risks detected by static analysis."
    fi
    echo ""
    echo "## Suggestions"
    echo ""
    echo "- Review test coverage for changed files"
    echo "- Verify edge cases for modified logic"
    echo "- Check if documentation needs updating"
    echo ""
    echo "---"
    echo "*Generated by claude-review on $(date +%Y-%m-%d)*"
} > "${OUTPUT:-/dev/stdout}"

if [[ -n "$OUTPUT" ]]; then
    echo "✅ Review saved to $OUTPUT"
fi

echo ""
echo "📊 Issues found: $TOTAL_ISSUES (🔒 $SECURITY security, 🐛 $BUGS bugs, ⚡ $PERF performance)"
