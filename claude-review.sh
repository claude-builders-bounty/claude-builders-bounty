#!/usr/bin/env bash
set -euo pipefail

# Claude Code PR Review Agent
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123
# Or:    ./claude-review.sh --pr 123 --repo owner/repo

PR_URL=""
REPO=""
PR_NUMBER=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --pr)
      if [[ "$2" =~ ^https?:// ]]; then
        PR_URL="$2"
        REPO=$(echo "$2" | sed -E 's|https://github.com/([^/]+/[^/]+)/pull/.*|\1|')
        PR_NUMBER=$(echo "$2" | grep -oE '[0-9]+$')
      else
        PR_NUMBER="$2"
      fi
      shift 2
      ;;
    --repo)
      REPO="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$REPO" || -z "$PR_NUMBER" ]]; then
  echo "Usage: $0 --pr <url|number> [--repo owner/repo]" >&2
  exit 1
fi

DIFF=$(gh pr diff "$PR_NUMBER" --repo "$REPO")
PR_INFO=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json title,body,files,additions,deletions)

PROMPT="You are a senior code reviewer. Analyze this PR and return a structured Markdown review.

PR Title: $(echo "$PR_INFO" | jq -r .title)
Files changed: $(echo "$PR_INFO" | jq '.files | length')
Additions: $(echo "$PR_INFO" | jq .additions), Deletions: $(echo "$PR_INFO" | jq .deletions)

Diff:
$DIFF

Return EXACTLY this format:

## Summary
(2-3 sentences describing what this PR does)

## Risks
- (list each risk as a bullet point)

## Suggestions
- (list each improvement suggestion as a bullet point)

## Confidence
(Low | Medium | High)"

echo "$PROMPT" | claude --print --model claude-sonnet-4-20250514
