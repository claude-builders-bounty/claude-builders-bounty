#!/usr/bin/env bash
# claude-review — AI-powered PR reviewer using Claude Code
#
# Usage:
#   claude-review --pr https://github.com/owner/repo/pull/123
#   claude-review --pr owner/repo#123
#   claude-review --diff file.diff

set -euo pipefail

SCRIPT_NAME="claude-review"
PR_URL=""
DIFF_FILE=""

# --- Parse arguments ---

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr)
            PR_URL="$2"
            shift 2
            ;;
        --diff)
            DIFF_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $SCRIPT_NAME --pr <url-or-shorthand> [--diff <file>]"
            echo ""
            echo "Options:"
            echo "  --pr   GitHub PR URL or shorthand (owner/repo#123)"
            echo "  --diff Local diff file to review"
            echo ""
            echo "Examples:"
            echo "  $SCRIPT_NAME --pr https://github.com/vercel/next.js/pull/999"
            echo "  $SCRIPT_NAME --pr vercel/next.js#999"
            echo "  $SCRIPT_NAME --diff changes.diff"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$PR_URL" ]] && [[ -z "$DIFF_FILE" ]]; then
    echo "Error: Provide --pr <url> or --diff <file>"
    exit 1
fi

# --- Fetch PR diff ---

DIFF=""
PR_TITLE=""
PR_BODY=""

if [[ -n "$PR_URL" ]]; then
    # Normalize shorthand: owner/repo#123 -> full args for gh
    if [[ "$PR_URL" =~ ^([^/]+/[^#]+)#([0-9]+)$ ]]; then
        REPO="${BASH_REMATCH[1]}"
        PR_NUM="${BASH_REMATCH[2]}"
    elif [[ "$PR_URL" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
        REPO="${BASH_REMATCH[1]}"
        PR_NUM="${BASH_REMATCH[2]}"
    else
        echo "Error: Cannot parse PR URL: $PR_URL"
        exit 1
    fi

    echo "Fetching PR #${PR_NUM} from ${REPO}..."
    DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO" 2>/dev/null || echo "FETCH_FAILED")
    if [[ "$DIFF" == "FETCH_FAILED" ]] || [[ -z "$DIFF" ]]; then
        echo "Error: Could not fetch diff. Check the PR URL and gh auth status."
        exit 1
    fi

    PR_TITLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json title -q '.title' 2>/dev/null || echo "Unknown")
    PR_BODY=$(gh pr view "$PR_NUM" --repo "$REPO" --json body -q '.body' 2>/dev/null | head -50 || echo "")
elif [[ -n "$DIFF_FILE" ]]; then
    if [[ ! -f "$DIFF_FILE" ]]; then
        echo "Error: File not found: $DIFF_FILE"
        exit 1
    fi
    DIFF=$(cat "$DIFF_FILE")
    PR_TITLE="Local diff review"
fi

# --- Truncate very large diffs ---

DIFF_LINES=$(echo "$DIFF" | wc -l | tr -d ' ')
if [[ "$DIFF_LINES" -gt 500 ]]; then
    DIFF=$(echo "$DIFF" | head -500)
    TRUNCATED="(Diff truncated from ${DIFF_LINES} to 500 lines)"
else
    TRUNCATED=""
fi

# --- Build review prompt ---

REVIEW_PROMPT="You are a senior code reviewer. Analyze this PR diff and produce a structured review.

PR Title: ${PR_TITLE}
PR Description: ${PR_BODY}
${TRUNCATED}

## Diff

\`\`\`diff
${DIFF}
\`\`\`

## Output format (follow exactly)

### Summary
[2-3 sentences describing what this PR does]

### Identified Risks
- [Risk 1]
- [Risk 2]
- [Or: No significant risks identified]

### Improvement Suggestions
- [Suggestion 1 with file:line reference if applicable]
- [Suggestion 2]
- [Or: No suggestions — changes look good]

### Confidence Score
[Low / Medium / High] — [one sentence explaining why]"

# --- Run review ---

echo "Reviewing..."
echo ""

claude -p \
    --model sonnet \
    --max-budget-usd 0.50 \
    --no-session-persistence \
    "$REVIEW_PROMPT" 2>/dev/null

echo ""
echo "---"
echo "Reviewed: ${REPO:-local}#${PR_NUM:-diff} (${DIFF_LINES} lines)"
