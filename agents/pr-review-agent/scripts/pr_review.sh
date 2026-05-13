
#!/usr/bin/env bash
set -euo pipefail

# Claude Code PR Review Agent
# Usage: ./pr_review.sh <pr-url>

PR_URL="${1:-}"
if [[ -z "$PR_URL" ]]; then
    echo "Error: PR URL is required" >&2
    echo "Usage: $0 <pr-url>" >&2
    exit 1
fi

# Validate PR URL format
if [[ ! "$PR_URL" =~ ^https://github\.com/.+/.+/pull/[0-9]+$ ]]; then
    echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/number" >&2
    exit 1
fi

# Check gh CLI availability
if ! command -v gh &>/dev/null; then
    echo "Error: GitHub CLI (gh) is not installed" >&2
    exit 1
fi

# Check authentication
if ! gh auth status &>/dev/null; then
    echo "Error: GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
    exit 1
fi

echo "🔍 Fetching PR details: $PR_URL" >&2

# Extract owner/repo from URL
REPO_FULL=$(echo "$PR_URL" | sed -E 's|https://github\.com/([^/]+/[^/]+)/pull/[0-9]+|\1|')
PR_NUMBER=$(echo "$PR_URL" | grep -oP '/pull/\K[0-9]+')

# Fetch PR metadata
PR_DATA=$(gh pr view "$PR_NUMBER" --repo "$REPO_FULL" --json title,body,author,state,additions,deletions,changedFiles,baseRefName,headRefName 2>/dev/null) || {
    echo "Error: Failed to fetch PR data. Check URL and permissions." >&2
    exit 1
}

# Fetch PR diff
PR_DIFF=$(gh pr diff "$PR_NUMBER" --repo "$REPO_FULL" 2>/dev/null) || {
    echo "Error: Failed to fetch PR diff." >&2
    exit 1
}

# Extract metadata
TITLE=$(echo "$PR_DATA" | jq -r '.title // "N/A"')
AUTHOR=$(echo "$PR_DATA" | jq -r '.author.login // "N/A"')
STATE=$(echo "$PR_DATA" | jq -r '.state // "N/A"')
ADDITIONS=$(echo "$PR_DATA" | jq -r '.additions // 0')
DELETIONS=$(echo "$PR_DATA" | jq -r '.deletions // 0')
CHANGED_FILES=$(echo "$PR_DATA" | jq -r '.changedFiles // 0')
BASE_BRANCH=$(echo "$PR_DATA" | jq -r '.baseRefName // "N/A"')
HEAD_BRANCH=$(echo "$PR_DATA" | jq -r '.headRefName // "N/A"')

echo "📊 Analyzing PR: $TITLE ($ADDITIONS additions, $DELETIONS deletions across $CHANGED_FILES files)" >&2

# Analyze diff for risks and suggestions
analyze_diff() {
    local diff_content="$1"
    local risks=()
    local suggestions=()
    local risk_score=0
    local has_security_issue=false
    local has_test_change=false
    local has_config_change=false
    local has_large_file=false
    local has_todo=false
    local has_debug=false
    local total_lines=0
    local file_count=0

    while IFS= read -r line; do
        # Count lines
        ((total_lines++))
        
        # Detect new files
        if [[ "$line" =~ ^\+\+\+ ]]; then
            ((file_count++))
        fi
        
        # Security risks
        if echo "$line" | grep -qiE '(password|secret|token|api.?key|credential|auth.?token)'; then
            if [[ "$line" =~ ^\+ ]]; then
                has_security_issue=true
                risks+=("Potential hardcoded credential detected")
            fi
        fi
        
        # SQL injection risk
        if echo "$line" | grep -qiE '(SELECT|INSERT|UPDATE|DELETE).*\$|execute\(|query\('; then
            if [[ "$line" =~ ^\+ ]]; then
                risks+=("Possible SQL injection vulnerability - use parameterized queries")
            fi
        fi
        
        # XSS risk
        if echo "$line" | grep -qiE '(innerHTML|outerHTML|dangerouslySetInnerHTML|v-html)'; then
            if [[ "$line" =~ ^\+ ]]; then
                risks+=("Potential XSS vulnerability - avoid raw HTML insertion")
            fi
        fi
        
        # Debug code
        if echo "$line" | grep -qiE '(console\.log|console\.debug|print_r|var_dump|dd\()'; then
            if [[ "$line" =~ ^\+ ]]; then
                has_debug=true
                risks+=("Debug code left in production")
            fi
        fi
        
        # TODO/FIXME
        if echo "$line" | grep -qiE '(TODO|FIXME|HACK|XXX)'; then
            if [[ "$line" =~ ^\+ ]]; then
                has_todo=true
                suggestions+=("Address TODO/FIXME comments before merging")
            fi
        fi
        
        # Large files
        if [[ "$line" =~ ^diff ]]; then
            has_large_file=false
        fi
        
        # Test files
        if echo "$line" | grep -qiE '(test|spec|__tests__)'; then
            if [[ "$line" =~ ^\+\+\+ ]]; then
                has_test_change=true
            fi
        fi
        
        # Config changes
        if echo "$line" | grep -qiE '(\.env|config\.|\.json|\.yaml|\.yml)'; then
            if [[ "$line" =~ ^\+\+\+ ]]; then
                has_config_change=true
            fi
        fi
        
        # Error handling
        if echo "$line" | grep -qiE 'catch\s*\(.*\)\s*\{'; then
            if [[ "$line" =~ ^\+ ]]; then
                suggestions+=("Ensure catch blocks have proper error handling, not just logging")
            fi
        fi
        
        # Magic numbers
        if echo "$line" | grep -qiE 'if\s*\(.*[=!]=.*[0-9]{3,}'; then
            if [[ "$line" =~ ^\+ ]]; then
                suggestions+=("Consider extracting magic numbers to named constants")
            fi
        fi
        
        # Long lines
        if [[ ${#line} -gt 120 ]] && [[ "$line" =~ ^\+ ]]; then
            suggestions+=("Line exceeds 120 characters - consider breaking into multiple lines")
        fi
        
    done <<< "$diff_content"
    
    # Calculate risk score
    if $has_security_issue; then ((risk_score += 3)); fi
    if $has_debug; then ((risk_score += 2)); fi
    if $has_todo; then ((risk_score += 1)); fi
    if [[ ${#risks[@]} -gt 3 ]]; then ((risk_score += 2)); fi
    
    # Calculate confidence
    local confidence=7
    if [[ $total_lines -gt 500 ]]; then
        confidence=6
    elif [[ $total_lines -lt 50 ]]; then
        confidence=9
    fi
    
    if $has_test_change; then
        ((confidence += 1))
    fi
    
    if [[ $risk_score -gt 5 ]]; then
        ((confidence -= 2))
    fi
    
    # Ensure confidence is between 1-10
    if [[ $confidence -lt 1 ]]; then confidence=1; fi
    if [[ $confidence -gt 10 ]]; then confidence=10; fi
    
    # Generate summary
    local summary=""
    if [[ $ADDITIONS -gt 0 ]] || [[ $DELETIONS -gt 0 ]]; then
        summary="This PR by **$AUTHOR** modifies **$CHANGED_FILES files** with **$ADDITIONS additions** and **$DELETIONS deletions** across the **$BASE_BRANCH → $HEAD_BRANCH** branches. "
        if $has_test_change; then
            summary+="The changes include test modifications, which is a good practice. "
        else
            summary+="No test changes were detected, which may require attention. "
        fi
        summary+="Overall, the changes are "
        if [[ $risk_score -lt 3 ]]; then
            summary+="low risk"
        elif [[ $risk_score -lt 6 ]]; then
            summary+="moderate risk"
        else
            summary+="high risk"
        fi
        summary+="."
    fi
    
    # Output structured review
    cat <<REVIEW