#!/bin/bash
# claude-review — AI-powered PR review via GitHub API + LLM
# By sami (sami-openlife) — autonomous AI agent
#
# Usage: bash claude-review.sh https://github.com/owner/repo/pull/123
# Requires: GITHUB_TOKEN env var, curl, python3
# Optional: ANTHROPIC_API_KEY for Claude, or OPENAI_API_KEY for GPT

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: claude-review <PR_URL>"
    echo "Example: claude-review https://github.com/owner/repo/pull/123"
    exit 1
fi

PR_URL="$1"

# Parse owner/repo/number from URL
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUM="${BASH_REMATCH[3]}"
else
    echo "Error: Invalid PR URL. Expected format: https://github.com/owner/repo/pull/123"
    exit 1
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN env var required"
    exit 1
fi

echo "📋 Reviewing PR #${PR_NUM} on ${OWNER}/${REPO}..."

# Fetch PR info
PR_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}")

PR_TITLE=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('title',''))")
PR_BODY=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('body','')[:1000])")
PR_AUTHOR=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('user',{}).get('login',''))")
PR_FILES=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('changed_files',0))")
PR_ADDITIONS=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('additions',0))")
PR_DELETIONS=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('deletions',0))")

# Fetch diff
DIFF=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}")

# Truncate diff if too large (keep first 8000 chars)
DIFF_TRUNCATED=$(echo "$DIFF" | head -c 8000)
if [ ${#DIFF} -gt 8000 ]; then
    DIFF_TRUNCATED="${DIFF_TRUNCATED}\n\n... [diff truncated, ${#DIFF} total chars]"
fi

# Build the review prompt
PROMPT="You are a senior code reviewer. Review this PR and provide structured feedback.

PR: ${OWNER}/${REPO}#${PR_NUM}
Title: ${PR_TITLE}
Author: ${PR_AUTHOR}
Files changed: ${PR_FILES} (+${PR_ADDITIONS} -${PR_DELETIONS})

Description:
${PR_BODY}

Diff:
${DIFF_TRUNCATED}

Respond in this exact Markdown format:

## PR Review: ${OWNER}/${REPO}#${PR_NUM}

### Summary
(2-3 sentences describing what this PR does)

### Identified Risks
- (list each risk with severity: 🔴 High / 🟡 Medium / 🟢 Low)

### Improvement Suggestions
- (actionable suggestions, reference specific files/lines when possible)

### Confidence Score
**[Low/Medium/High]** — (one sentence explaining your confidence level)

---
*Reviewed by claude-review (sami-openlife)*"

# Try Anthropic first, then OpenAI
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "🤖 Using Claude for review..."
    REVIEW=$(python3 -c "
import json, urllib.request
data = json.dumps({
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 2000,
    'messages': [{'role': 'user', 'content': '''$PROMPT'''}]
}).encode()
req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=data, headers={
    'x-api-key': '${ANTHROPIC_API_KEY}',
    'anthropic-version': '2023-06-01',
    'Content-Type': 'application/json'
})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(result['content'][0]['text'])
")
elif [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "🤖 Using GPT for review..."
    REVIEW=$(python3 -c "
import json, urllib.request
data = json.dumps({
    'model': 'gpt-4o-mini',
    'messages': [{'role': 'user', 'content': '''$PROMPT'''}],
    'max_tokens': 2000
}).encode()
req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=data, headers={
    'Authorization': 'Bearer ${OPENAI_API_KEY}',
    'Content-Type': 'application/json'
})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(result['choices'][0]['message']['content'])
")
else
    # Fallback: rule-based review without LLM
    echo "⚠️ No API key found. Using rule-based review..."
    REVIEW="## PR Review: ${OWNER}/${REPO}#${PR_NUM}

### Summary
PR by ${PR_AUTHOR} modifying ${PR_FILES} files (+${PR_ADDITIONS} -${PR_DELETIONS}). Title: \"${PR_TITLE}\".

### Identified Risks"

    # Simple pattern-based risk detection
    RISKS=""
    echo "$DIFF" | grep -qiE 'TODO|FIXME|HACK' && RISKS="${RISKS}\n- 🟡 Medium: Contains TODO/FIXME/HACK comments"
    echo "$DIFF" | grep -qiE 'console\.log|print\(' && RISKS="${RISKS}\n- 🟢 Low: Contains debug logging statements"
    echo "$DIFF" | grep -qiE 'password|secret|api.key|token' && RISKS="${RISKS}\n- 🔴 High: Potential hardcoded credentials"
    echo "$DIFF" | grep -qiE 'rm -rf|DROP TABLE|DELETE FROM' && RISKS="${RISKS}\n- 🔴 High: Contains destructive operations"
    [ ${PR_ADDITIONS} -gt 500 ] && RISKS="${RISKS}\n- 🟡 Medium: Large PR (${PR_ADDITIONS} additions) — consider splitting"
    [ -z "$RISKS" ] && RISKS="\n- 🟢 Low: No obvious risks detected"

    REVIEW="${REVIEW}${RISKS}

### Improvement Suggestions
- Review the ${PR_FILES} changed files for edge cases
- Ensure tests cover the new/modified code paths
- Verify no sensitive data is exposed in the changes

### Confidence Score
**Low** — Rule-based analysis only. Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered review.

---
*Reviewed by claude-review (sami-openlife)*"
fi

echo ""
echo "$REVIEW"
