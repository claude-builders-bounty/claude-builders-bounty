#!/usr/bin/env bash
# claude-review.sh — CLI wrapper for Claude-powered PR review
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123

set -euo pipefail

PR_URL=""
POST_COMMENT=false
MODEL="claude-sonnet-4-20250514"

usage() {
  cat <<EOF
Usage: $0 --pr <PR_URL> [--post] [--model <MODEL>]

Options:
  --pr    GitHub PR URL (required)
  --post  Post review as PR comment
  --model Claude model to use (default: $MODEL)
  -h      Show this help

Environment:
  ANTHROPIC_API_KEY  Required for Claude API access

Examples:
  $0 --pr https://github.com/owner/repo/pull/123
  $0 --pr https://github.com/owner/repo/pull/123 --post
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)   PR_URL="$2"; shift 2 ;;
    --post) POST_COMMENT=true; shift ;;
    --model) MODEL="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required" >&2; exit 1
fi
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "Error: ANTHROPIC_API_KEY not set" >&2; exit 1
fi

# Parse PR URL: .../owner/repo/pull/123
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
else
  echo "Error: Invalid PR URL: $PR_URL" >&2; exit 1
fi

echo "=> Fetching diff for $OWNER/$REPO#$PR_NUM ..."
DIFF=$(gh pr diff "$PR_NUM" --repo "$OWNER/$REPO" 2>/dev/null)

if [[ -z "$DIFF" ]]; then
  echo "Error: Empty diff. Check PR URL and gh auth status." >&2; exit 1
fi

echo "=> Sending to Claude ($MODEL) for review ..."
PAYLOAD=$(jq -n \
  --arg model "$MODEL" \
  --arg diff "$DIFF" \
  '{
    model: $model,
    max_tokens: 4096,
    messages: [{
      role: "user",
      content: ("You are a senior code reviewer. Review this PR diff and output structured Markdown with:\n\n## Summary\n2-3 sentence summary of changes.\n\n## Risks\nList risks with severity (Critical/High/Medium/Low).\n\n## Suggestions\nNumbered improvement suggestions.\n\n## Confidence\nOverall confidence: Low/Medium/High\n\n```\n" + $diff + "\n```")
    }]
  }')

REVIEW=$(curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "$PAYLOAD" | jq -r '.content[0].text // .error.message // "API error"')

echo ""
echo "========== PR REVIEW =========="
echo "$REVIEW"
echo "================================"

if $POST_COMMENT; then
  echo "=> Posting review as PR comment ..."
  gh pr comment "$PR_NUM" --repo "$OWNER/$REPO" --body "$REVIEW"
  echo "=> Review posted."
fi
