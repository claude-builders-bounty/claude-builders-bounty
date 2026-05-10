#!/usr/bin/env bash
set -euo pipefail

# Claude Code PR Reviewer Agent
# Usage: claude-review --pr https://github.com/owner/repo/pull/123

PR_URL=""
OUTPUT_FORMAT="markdown"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --format) OUTPUT_FORMAT="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: claude-review --pr <PR_URL>"
            echo ""
            echo "Options:"
            echo "  --pr        GitHub PR URL (required)"
            echo "  --format    Output format: markdown, json (default: markdown)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$PR_URL" ]]; then
    echo "Error: --pr URL is required" >&2
    exit 1
fi

# Parse PR URL
IFS='/' read -ra PARTS <<< "$PR_URL"
OWNER="${PARTS[3]}"
REPO="${PARTS[4]}"
PR_NUM="${PARTS[6]}"

echo "🔍 Reviewing PR: ${OWNER}/${REPO}#${PR_NUM}" >&2

# Fetch PR diff
DIFF=$(curl -sL "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}"     -H "Accept: application/vnd.github.v3.diff" 2>/dev/null)

if [[ -z "$DIFF" ]] || [[ "$DIFF" == *"Not Found"* ]]; then
    echo "Error: Could not fetch PR diff" >&2
    exit 1
fi

# Fetch PR metadata
PR_META=$(curl -s "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}" 2>/dev/null)
TITLE=$(echo "$PR_META" | python3 -c "import json,sys; print(json.load(sys.stdin).get('title',''))" 2>/dev/null)
BODY=$(echo "$PR_META" | python3 -c "import json,sys; print(json.load(sys.stdin).get('body','')[:500])" 2>/dev/null)
CHANGED_FILES=$(echo "$PR_META" | python3 -c "import json,sys; print(json.load(sys.stdin).get('changed_files',0))" 2>/dev/null)
ADDITIONS=$(echo "$PR_META" | python3 -c "import json,sys; print(json.load(sys.stdin).get('additions',0))" 2>/dev/null)
DELETIONS=$(echo "$PR_META" | python3 -c "import json,sys; print(json.load(sys.stdin).get('deletions',0))" 2>/dev/null)

# Save diff for Claude analysis
DIFF_FILE=$(mktemp /tmp/pr-diff-XXXXXX.diff)
echo "$DIFF" > "$DIFF_FILE"

# Generate review using Claude
REVIEW=$(cat << REVIEW_EOF
You are a senior code reviewer. Analyze this PR diff and provide a structured review.

PR: ${OWNER}/${REPO}#${PR_NUM}
Title: ${TITLE}
Files changed: ${CHANGED_FILES}
+${ADDITIONS} / -${DELETIONS} lines

Provide your review in this EXACT format:

## Summary
(2-3 sentences describing what this PR does)

## Risks
- (risk 1)
- (risk 2)
- (risk 3)

## Suggestions
- (suggestion 1)
- (suggestion 2)

## Confidence
(Low / Medium / High)

## Verdict
(APPROVE / REQUEST_CHANGES / COMMENT)

---

Diff:
$(head -500 "$DIFF_FILE")
REVIEW_EOF
)

# Output the review prompt (to be piped to Claude)
echo "$REVIEW"

# Cleanup
rm -f "$DIFF_FILE"
