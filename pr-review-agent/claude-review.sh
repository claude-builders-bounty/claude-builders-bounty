#!/bin/bash
# Claude PR Review Agent - Bounty #4
set -euo pipefail

usage() {
  echo "Usage: $0 --pr <PR_URL> [--api-key <KEY>]"
  exit 1
}

PR_URL=""
API_KEY="${CLAUDE_API_KEY:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --api-key) API_KEY="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[ -z "$PR_URL" ] && usage
[ -z "$API_KEY" ] && { echo "Error: CLAUDE_API_KEY not set. Use --api-key or export CLAUDE_API_KEY."; exit 1; }

# Fetch PR diff using GitHub API (no auth needed for public repos)
echo "Fetching PR diff for $PR_URL..."
DIFF=$(curl -s -H "Accept: application/vnd.github.v3.diff" "${PR_URL}.diff" 2>/dev/null)
if [ -z "$DIFF" ]; then
  echo "Error: Could not fetch diff. Ensure the PR URL is correct and public."
  exit 1
fi

# Truncate diff to avoid exceeding token limits (approx 50KB max for Claude)
DIFF_TRUNC=$(echo "$DIFF" | head -c 50000)

# Prepare Claude API prompt
PROMPT="You are a senior code reviewer. Analyze the following PR diff and provide a structured Markdown review with:
- **Summary of changes** (2-3 sentences)
- **Identified risks** (list)
- **Improvement suggestions** (list)
- **Confidence score** (Low/Medium/High)

PR Diff:
$DIFF_TRUNC"

# Call Claude API using the Messages endpoint
RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1500,
    "messages": [
      {"role": "user", "content": "'"$(echo "$PROMPT" | jq -Rs .)"'"}
    ]
  }')

# Extract the review text
REVIEW=$(echo "$RESPONSE" | jq -r '.content[0].text' 2>/dev/null)
if [ -z "$REVIEW" ]; then
  echo "Error: Claude API call failed. Response:"
  echo "$RESPONSE"
  exit 1
fi

echo "$REVIEW"
