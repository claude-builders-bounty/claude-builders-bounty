#!/usr/bin/env bash
# claude-review — Claude Code sub-agent that reviews a PR and posts a structured comment
# Usage: claude-review --pr https://github.com/owner/repo/pull/123 [--post]
set -euo pipefail

PR_URL=""
POST_COMMENT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --post) POST_COMMENT=true; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Usage: claude-review --pr <url> [--post]" >&2
  exit 1
fi

# Extract owner/repo and number from URL
OWNER_REPO=$(echo "$PR_URL" | sed -E 's#https://github.com/([^/]+/[^/]+)/pull/([0-9]+).*#\1#')
PR_NUMBER=$(echo "$PR_URL" | sed -E 's#.*/pull/([0-9]+).*#\1#')

if [[ -z "$OWNER_REPO" || -z "$PR_NUMBER" ]]; then
  echo "Failed to parse PR URL: $PR_URL" >&2
  exit 1
fi

# Fetch diff
DIFF=$(gh pr diff "$PR_NUMBER" --repo "$OWNER_REPO")

# Build prompt
PROMPT="You are an expert code reviewer. Analyze the following GitHub PR diff and produce a structured Markdown review with exactly these sections:

## Summary
(2-3 sentences describing what this PR does)

## Identified Risks
- (bullet list of potential issues, edge cases, or regressions)

## Improvement Suggestions
- (bullet list of actionable improvements)

## Confidence Score
(Low / Medium / High — based on how well you can assess correctness from the diff alone)

Be concise, specific, and reference file names or line ranges when possible. Do NOT include any preamble or closing remarks outside these four sections.

--- DIFF START ---
$DIFF
--- DIFF END ---"

# Call Claude via CLI (non-interactive, single turn)
REVIEW=$(echo "$PROMPT" | claude --print --model claude-sonnet-5[1m] 2>/dev/null || echo "ERROR: claude CLI invocation failed")

echo "$REVIEW"

# Optionally post as PR comment
if [[ "$POST_COMMENT" == true ]]; then
  gh pr comment "$PR_NUMBER" --repo "$OWNER_REPO" --body "$REVIEW"
  echo "✅ Review posted to $PR_URL"
fi
