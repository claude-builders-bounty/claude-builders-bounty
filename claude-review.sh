#!/usr/bin/env bash
# Claude PR Review CLI — reviews a PR diff and outputs structured Markdown
# Usage: ./claude-review.sh https://github.com/owner/repo/pull/123
set -euo pipefail

PR_URL="${1:-}"
if [ -z "$PR_URL" ]; then
    echo "Usage: $0 <PR_URL>" >&2
    echo "Example: $0 https://github.com/owner/repo/pull/123" >&2
    exit 1
fi

# Parse owner/repo/number from URL
OWNER=$(echo "$PR_URL" | sed -E 's|https://github.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1|')
REPO=$(echo "$PR_URL" | sed -E 's|https://github.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\2|')
NUMBER=$(echo "$PR_URL" | sed -E 's|https://github.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\3|')

if [ -z "$OWNER" ] || [ -z "$REPO" ] || [ -z "$NUMBER" ]; then
    echo "Error: Could not parse PR URL: $PR_URL" >&2
    exit 1
fi

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H \"Authorization: token $TOKEN\""
fi

# Fetch PR metadata
PR_DATA=$(curl -s -H "Accept: application/vnd.github.v3+json" \
    ${TOKEN:+-H "Authorization: token $TOKEN"} \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$NUMBER")

TITLE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title',''))" 2>/dev/null)
BASE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('base',{}).get('ref','main'))" 2>/dev/null)
HEAD=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('head',{}).get('ref',''))" 2>/dev/null)

# Fetch diff
DIFF=$(curl -s -H "Accept: application/vnd.github.v3.diff" \
    ${TOKEN:+-H "Authorization: token $TOKEN"} \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$NUMBER")

if [ -z "$DIFF" ]; then
    echo "Error: Failed to fetch diff for $PR_URL" >&2
    exit 1
fi

DIFF_TRUNCATED=$(echo "$DIFF" | head -c 50000)

PROMPT="Review this PR and output a structured Markdown comment.

PR: $OWNER/$REPO#$NUMBER — $TITLE
Base: $BASE ← Head: $HEAD

## Output Format (use exactly):

### Summary
One-paragraph overview of what this PR does.

### ✅ Strengths
- Bullet list of good decisions, patterns, or implementations.

### ⚠️ Suggestions
- Bullet list of improvements (non-blocking). Each: **what** + **why**.

### 🐛 Issues
- Bullet list of bugs/security/correctness problems. Each: **severity** (Critical/Major/Minor) + **description** + **fix**.

### Verdict
One of: APPROVE, REQUEST_CHANGES, or COMMENT with one-line reasoning.

## Rules
- Reference file names and line ranges.
- Don't repeat the diff.
- Focus on logic, security, performance, maintainability.
- Skip style nits unless they impact readability.

## Diff
\`\`\`diff
$DIFF_TRUNCATED
\`\`\`"

# Try claude CLI first, fallback to echo
if command -v claude &>/dev/null; then
    echo "$PROMPT" | claude --print 2>/dev/null
else
    echo "⚠️  Claude CLI not found. Install: npm install -g @anthropic-ai/claude-code" >&2
    echo "Falling back to raw diff summary..." >&2
    echo ""
    echo "### Summary"
    echo "PR #$NUMBER: $TITLE ($BASE ← $HEAD)"
    echo ""
    echo "### Diff Stats"
    echo "$DIFF" | grep -c '^+' | xargs -I{} echo "- Lines added: {}"
    echo "$DIFF" | grep -c '^-' | xargs -I{} echo "- Lines removed: {}"
    echo "$DIFF" | grep '^diff --git' | sed 's|diff --git a/||;s| b/.*||' | head -10 | xargs -I{} echo "- File: {}"
fi
