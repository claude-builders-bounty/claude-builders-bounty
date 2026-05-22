#!/usr/bin/env bash
# review-pr.sh - CLI tool to review a GitHub PR using Claude Code
# Usage: ./scripts/review-pr.sh <PR_URL or owner/repo#number>
#
# Requirements: gh (GitHub CLI), claude (Claude Code CLI)
# Environment: ANTHROPIC_API_KEY must be set

set -euo pipefail

PR_REF="${1:?Usage: review-pr.sh <PR_URL or owner/repo#number>}"

# Normalize PR reference to owner/repo#number format
if [[ "$PR_REF" == http* ]]; then
  # Extract from URL: https://github.com/owner/repo/pull/123
  PR_REF=$(echo "$PR_REF" | sed -E 's|https://github.com/([^/]+)/([^/]+)/pull/([0-9]+)|\1/\2#\3|')
fi

echo "🔍 Fetching PR: $PR_REF"

# Fetch PR info
PR_INFO=$(gh pr view "$PR_REF" --json title,body,files,additions,deletions,url 2>/dev/null) || {
  echo "❌ Could not fetch PR. Check that the repo is public and gh is authenticated."
  exit 1
}

PR_TITLE=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).title))")
PR_URL=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).url))")
PR_BODY=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).body||''))")
PR_FILES=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).files.length))")
PR_ADDS=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).additions))")
PR_DELS=$(echo "$PR_INFO" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).deletions))")

echo "📋 PR: $PR_TITLE ($PR_FILES files, +$PR_ADDS/-$PR_DELS)"
echo "📝 Fetching diff..."

PR_DIFF=$(gh pr diff "$PR_REF" 2>/dev/null) || {
  echo "❌ Could not fetch diff."
  exit 1
}

# Build the review prompt
PROMPT="You are a senior code reviewer. Review the following pull request and produce a structured Markdown review.

## PR: $PR_TITLE

$PR_BODY

## Diff
\`\`\`
$PR_DIFF
\`\`\`

Produce a structured review with:
1. **Summary** (2-3 sentences of what this PR does)
2. **Risks** (list of identified risks)
3. **Improvement Suggestions** (list of suggestions)
4. **Verdict** (APPROVE / REQUEST_CHANGES / COMMENT with justification)

Output ONLY the Markdown review, no preamble."

echo "🤖 Running Claude Code review..."
REVIEW=$(echo "$PROMPT" | claude --model sonnet --print 2>/dev/null) || {
  echo "⚠️  Could not run Claude Code. Outputting prompt for manual review."
  echo "$PROMPT"
  exit 0
}

echo ""
echo "=== REVIEW ==="
echo "$REVIEW"
echo "=== END REVIEW ==="
echo ""

# Post the review as a PR comment
echo "📤 Posting review to PR..."
gh pr comment "$PR_REF" --body "$REVIEW" 2>/dev/null && \
  echo "✅ Review posted to $PR_URL" || \
  echo "⚠️  Could not post comment. Review output above."
