#!/usr/bin/env bash
set -euo pipefail

VERSION="1.0.0"

usage() {
  cat <<EOF
claude-review v$VERSION — AI-powered PR review agent

Usage:
  claude-review --pr <pr-url>
  claude-review --pr https://github.com/owner/repo/pull/123

Options:
  --pr <url>         GitHub PR URL to review
  --model <model>    Claude model (default: claude-sonnet-4-20250514)
  --help             Show this help
EOF
  exit 0
}

PR_URL=""
MODEL="claude-sonnet-4-20250514"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required"
  usage
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "Error: ANTHROPIC_API_KEY environment variable is required"
  exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Error: GITHUB_TOKEN environment variable is required"
  exit 1
fi

OWNER_REPO=$(echo "$PR_URL" | sed -E 's|https://github.com/||' | sed -E 's|/pull/[0-9]+||')
PR_NUMBER=$(echo "$PR_URL" | sed -E 's|.*/pull/||')

echo "🔍 Fetching PR #$PR_NUMBER from $OWNER_REPO ..."

DIFF=$(curl -s -L \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUMBER")

PR_DATA=$(curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUMBER")

PR_TITLE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title',''))" 2>/dev/null || echo "")
PR_BODY=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body',''))" 2>/dev/null || echo "")

echo "✅ PR fetched: $PR_TITLE"
echo "🧠 Analyzing with Claude ($MODEL) ..."

RESPONSE=$(curl -s -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"max_tokens\": 4096,
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"You are a senior code reviewer. Analyze the following PR diff and provide a structured review.\\n\\nPR Title: $PR_TITLE\\nPR Description: $PR_BODY\\n\\nDiff:\\n\`\`\`diff\\n$DIFF\\n\`\`\`\\n\\nProvide your review in this exact Markdown format:\\n\\n## Summary of Changes\\n(2-3 sentences)\\n\\n## Identified Risks\\n- Risk 1\\n- Risk 2\\n\\n## Improvement Suggestions\\n- Suggestion 1\\n- Suggestion 2\\n\\n## Confidence Score\\n**Low / Medium / High**\\n\\n---\\n*Reviewed by claude-review v$VERSION*\"}]
  }")

SUMMARY=$(echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d['content'][0]['text']
print(content)
" 2>/dev/null || echo "Error: Claude API request failed")

echo ""
echo "═══════════════════════════════════════════"
echo "  PR REVIEW — $OWNER_REPO#$PR_NUMBER"
echo "  $PR_TITLE"
echo "═══════════════════════════════════════════"
echo ""
echo "$SUMMARY"
echo ""
echo "═══════════════════════════════════════════"
