#!/usr/bin/env bash
set -euo pipefail

# Claude Code PR Review Agent
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123
# Outputs structured Markdown review to stdout

PR_URL=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$PR_URL" ]; then
  echo "Usage: $0 --pr <pull_request_url>" >&2
  exit 1
fi

# Parse owner/repo/pr_number from URL
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"
else
  echo "Error: Invalid GitHub PR URL format" >&2
  exit 1
fi

# Fetch PR diff via gh CLI
DIFF=$(gh pr diff "$PR_NUMBER" --repo "$OWNER/$REPO" 2>/dev/null)
if [ -z "$DIFF" ]; then
  echo "Error: Could not fetch PR diff. Check URL and authentication." >&2
  exit 1
fi

# Fetch PR metadata
PR_INFO=$(gh pr view "$PR_NUMBER" --repo "$OWNER/$REPO" --json title,body,files,additions,deletions,changedFiles 2>/dev/null)

TITLE=$(echo "$PR_INFO" | jq -r '.title')
BODY=$(echo "$PR_INFO" | jq -r '.body // "No description provided"')
FILES_CHANGED=$(echo "$PR_INFO" | jq -r '.changedFiles')
ADDITIONS=$(echo "$PR_INFO" | jq -r '.additions')
DELETIONS=$(echo "$PR_INFO" | jq -r '.deletions')

# Generate review using Claude API via GhostCLI
REVIEW_PROMPT="You are a senior code reviewer. Analyze this PR diff and produce a structured Markdown review.

PR Title: $TITLE
Files Changed: $FILES_CHANGED (+$ADDITIONS / -$DELETIONS)

Diff:
$DIFF

Output EXACTLY this format (no extra text):

## Summary
(2-3 sentences describing what this PR does and its purpose)

## Risks
- (list each identified risk as a bullet point, or 'None identified' if none)

## Suggestions
- (list each improvement suggestion as a bullet point, or 'None' if none)

## Confidence
(Low | Medium | High) — (brief reason for confidence level)"

REVIEW=$(echo "$REVIEW_PROMPT" | claude --print --model claude-sonnet-5[1m] 2>/dev/null || echo "## Summary
Could not generate AI review. Ensure Claude CLI is configured with GhostCLI provider.

## Risks
- Unable to analyze without AI assistance

## Suggestions
- Verify Claude CLI installation and GhostCLI API key configuration

## Confidence
Low — AI review generation failed")

# Format final output
OUTPUT="# PR Review: $TITLE

**Repository:** \`$OWNER/$REPO\` | **PR:** #$PR_NUMBER | **Files:** $FILES_CHANGED (+$ADDITIONS/-$DELETIONS)
**Reviewed at:** $(date -u +%Y-%m-%dT%H:%M:%SZ)

---

$REVIEW"

if [ -n "$OUTPUT_FILE" ]; then
  echo "$OUTPUT" > "$OUTPUT_FILE"
  echo "Review written to $OUTPUT_FILE"
else
  echo "$OUTPUT"
fi
