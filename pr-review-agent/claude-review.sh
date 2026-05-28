#!/usr/bin/env bash
# claude-review — CLI tool to review GitHub PRs using Claude Code
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
#
# Requirements: gh (GitHub CLI), claude (Claude Code CLI)
# Bounty: #4 — $150

set -euo pipefail

# --- Parse arguments ---
PR_URL=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --pr)
            PR_URL="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: claude-review --pr <github-pr-url>"
            echo ""
            echo "Options:"
            echo "  --pr URL       GitHub PR URL (required)"
            echo "  --output FILE  Write output to file instead of stdout"
            echo "  --help         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$PR_URL" ]]; then
    echo "Error: --pr URL is required" >&2
    echo "Usage: claude-review --pr https://github.com/owner/repo/pull/123" >&2
    exit 1
fi

# --- Extract PR info from URL ---
# Supports: https://github.com/owner/repo/pull/123
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    PR_NUM="${BASH_REMATCH[3]}"
else
    echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123" >&2
    exit 1
fi

echo "🔍 Reviewing PR #${PR_NUM} in ${REPO}..." >&2

# --- Fetch PR metadata ---
PR_INFO=$(gh pr view "$PR_NUM" --repo "$REPO" --json title,body,author,additions,deletions,changedFiles,baseRefName,headRefName 2>/dev/null || echo "")

if [[ -z "$PR_INFO" ]]; then
    echo "Error: Could not fetch PR info. Check the URL and your gh auth." >&2
    exit 1
fi

PR_TITLE=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title',''))")
PR_BODY=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body','')[:2000])")
PR_AUTHOR=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('author',{}).get('login',''))")
PR_ADDITIONS=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('additions',0))")
PR_DELETIONS=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('deletions',0))")
PR_FILES=$(echo "$PR_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('changedFiles',0))")

# --- Fetch PR diff ---
PR_DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO" 2>/dev/null || echo "")

if [[ -z "$PR_DIFF" ]]; then
    echo "Warning: Could not fetch diff. Reviewing based on metadata only." >&2
fi

# Truncate diff if too long (Claude context limits)
DIFF_LEN=${#PR_DIFF}
if [[ $DIFF_LEN -gt 15000 ]]; then
    PR_DIFF="${PR_DIFF:0:15000}

... [Diff truncated at 15000 chars — ${DIFF_LEN} total chars]"
fi

# --- Build the review prompt ---
PROMPT="You are a senior code reviewer. Analyze this GitHub PR and provide a structured review.

## PR Info
- **Repository:** ${REPO}
- **PR #${PR_NUM}:** ${PR_TITLE}
- **Author:** ${PR_AUTHOR}
- **Changes:** +${PR_ADDITIONS} -${PR_DELETIONS} across ${PR_FILES} files

## PR Description
${PR_BODY}

## Diff
\`\`\`diff
${PR_DIFF}
\`\`\`

## Required Output Format

Respond with ONLY this Markdown structure (no preamble):

### Summary
[2-3 sentence summary of what this PR does and why]

### Risks
- [risk 1]
- [risk 2]
- [risk 3 if applicable]

### Suggestions
- [improvement suggestion 1]
- [improvement suggestion 2]
- [improvement suggestion 3 if applicable]

### Confidence: [Low/Medium/High]
[1 sentence explaining the confidence level]"

# --- Send to Claude ---
# Try claude CLI first (Claude Code), fall back to API
REVIEW=""

if command -v claude &>/dev/null; then
    echo "  Using Claude Code CLI..." >&2
    REVIEW=$(echo "$PROMPT" | claude --print 2>/dev/null || echo "")
fi

# Fallback: use Anthropic API directly
if [[ -z "$REVIEW" ]] && [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "  Using Anthropic API..." >&2
    API_RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: ${ANTHROPIC_API_KEY}" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "$(python3 -c "
import json, sys
prompt = '''$PROMPT'''
print(json.dumps({
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 2000,
    'messages': [{'role': 'user', 'content': prompt}]
}))
")" 2>/dev/null || echo "")
    REVIEW=$(echo "$API_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content',[{}])[0].get('text',''))" 2>/dev/null || echo "")
fi

if [[ -z "$REVIEW" ]]; then
    echo "Error: Could not get review from Claude. Ensure 'claude' CLI or ANTHROPIC_API_KEY is available." >&2
    exit 1
fi

# --- Format final output ---
OUTPUT="# PR Review: ${REPO}#${PR_NUM}

**PR:** [${PR_TITLE}](${PR_URL})
**Author:** @${PR_AUTHOR}
**Changes:** +${PR_ADDITIONS} / -${PR_DELETIONS} across ${PR_FILES} files

---

${REVIEW}

---
*Reviewed by claude-review on $(date -u +%Y-%m-%d)*"

# --- Output ---
if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$OUTPUT" > "$OUTPUT_FILE"
    echo "✅ Review written to: ${OUTPUT_FILE}" >&2
else
    echo "$OUTPUT"
fi
