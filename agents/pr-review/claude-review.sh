#!/usr/bin/env bash
#
# claude-review - Claude Code PR Review Agent
#
# Usage:
#   claude-review --pr <github-pr-url>
#   claude-review --pr https://github.com/owner/repo/pull/123
#
# Requirements:
#   - gh (GitHub CLI) authenticated
#   - claude (Claude Code CLI) OR ANTHROPIC_API_KEY env var
#
set -euo pipefail

VERSION="1.0.0"

# ── Helpers ──────────────────────────────────────────────────────────────────

usage() {
  cat <<'EOF'
claude-review - AI-powered PR review using Claude

USAGE:
    claude-review --pr <github-pr-url> [OPTIONS]

OPTIONS:
    --pr <url>        GitHub pull request URL (required)
    --model <model>   Claude model to use (default: claude-sonnet-4-20250514)
    --output <file>   Write review to file instead of stdout
    --format <fmt>    Output format: markdown (default) or json
    --verbose         Show debug information
    --version         Print version
    --help            Show this help message

EXAMPLES:
    claude-review --pr https://github.com/facebook/react/pull/28000
    claude-review --pr https://github.com/owner/repo/pull/42 --output review.md
    claude-review --pr https://github.com/owner/repo/pull/42 --format json

ENVIRONMENT:
    ANTHROPIC_API_KEY   Required if 'claude' CLI is not installed
    CLAUDE_MODEL        Override default model
EOF
  exit 0
}

die() {
  echo "error: $*" >&2
  exit 1
}

info() {
  if [[ "${VERBOSE:-}" == "true" ]]; then
    echo "[info] $*" >&2
  fi
}

# ── Parse Arguments ──────────────────────────────────────────────────────────

PR_URL=""
MODEL="${CLAUDE_MODEL:-claude-sonnet-4-20250514}"
OUTPUT=""
FORMAT="markdown"
VERBOSE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR_URL="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE="true"
      shift
      ;;
    --version)
      echo "claude-review v${VERSION}"
      exit 0
      ;;
    --help|-h)
      usage
      ;;
    *)
      die "unknown option: $1 (use --help for usage)"
      ;;
  esac
done

[[ -z "$PR_URL" ]] && die "missing --pr <url> (use --help for usage)"

# ── Validate PR URL ─────────────────────────────────────────────────────────

# Extract owner/repo and PR number from URL
if [[ "$PR_URL" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUMBER="${BASH_REMATCH[2]}"
else
  die "invalid PR URL: $PR_URL (expected https://github.com/owner/repo/pull/123)"
fi

info "Repository: $REPO"
info "PR Number:  #$PR_NUMBER"

# ── Check Dependencies ──────────────────────────────────────────────────────

command -v gh &>/dev/null || die "'gh' (GitHub CLI) is required but not found. Install: https://cli.github.com"

# Check gh auth
gh auth status &>/dev/null 2>&1 || die "'gh' is not authenticated. Run: gh auth login"

# Determine Claude backend
USE_CLAUDE_CLI=false
if command -v claude &>/dev/null; then
  USE_CLAUDE_CLI=true
  info "Using Claude CLI"
elif [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  info "Using Anthropic API directly"
else
  die "Either 'claude' CLI or ANTHROPIC_API_KEY is required"
fi

# ── Fetch PR Data ────────────────────────────────────────────────────────────

info "Fetching PR metadata..."
PR_META=$(gh pr view "$PR_NUMBER" \
  --repo "$REPO" \
  --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,labels,state \
  2>/dev/null) || die "failed to fetch PR metadata (check repo access)"

PR_TITLE=$(echo "$PR_META" | gh pr view "$PR_NUMBER" --repo "$REPO" --json title -q .title 2>/dev/null || echo "")
PR_AUTHOR=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('author',{}).get('login','unknown'))" 2>/dev/null || echo "unknown")
PR_BASE=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('baseRefName','main'))" 2>/dev/null || echo "main")
PR_HEAD=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('headRefName','unknown'))" 2>/dev/null || echo "unknown")
PR_ADDITIONS=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('additions',0))" 2>/dev/null || echo "0")
PR_DELETIONS=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('deletions',0))" 2>/dev/null || echo "0")
PR_CHANGED=$(echo "$PR_META" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('changedFiles',0))" 2>/dev/null || echo "0")

info "Title:    $PR_TITLE"
info "Author:   $PR_AUTHOR"
info "Branch:   $PR_HEAD -> $PR_BASE"
info "Changes:  +$PR_ADDITIONS / -$PR_DELETIONS in $PR_CHANGED files"

info "Fetching PR diff..."
PR_DIFF=$(gh pr diff "$PR_NUMBER" --repo "$REPO" 2>/dev/null) || die "failed to fetch PR diff"

# Truncate very large diffs to stay within context limits
DIFF_LINES=$(echo "$PR_DIFF" | wc -l)
MAX_DIFF_LINES=3000
if [[ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]]; then
  info "Diff is $DIFF_LINES lines, truncating to $MAX_DIFF_LINES"
  PR_DIFF=$(echo "$PR_DIFF" | head -n "$MAX_DIFF_LINES")
  PR_DIFF="${PR_DIFF}

... [diff truncated at ${MAX_DIFF_LINES} lines — ${DIFF_LINES} total]"
fi

# ── Build Prompt ─────────────────────────────────────────────────────────────

REVIEW_PROMPT="You are a senior software engineer performing a thorough code review on a GitHub pull request. Analyze the PR metadata and diff below and produce a structured review.

## PR Metadata
- **Title:** ${PR_TITLE}
- **Author:** ${PR_AUTHOR}
- **Branch:** ${PR_HEAD} -> ${PR_BASE}
- **Stats:** +${PR_ADDITIONS} / -${PR_DELETIONS} across ${PR_CHANGED} files

## PR Diff
\`\`\`diff
${PR_DIFF}
\`\`\`

## Instructions
Produce a review in the following Markdown structure. Be specific, cite file names and line numbers where applicable, and be constructive.

### Summary
Write 2-3 sentences summarizing what this PR does, the approach taken, and the scope of changes.

### Identified Risks
List specific risks, including:
- Security concerns (injection, auth, data exposure)
- Performance issues (N+1 queries, unnecessary allocations, missing indexes)
- Correctness bugs or edge cases
- Breaking changes or backward compatibility
- Missing error handling or validation

If there are no significant risks, state that explicitly.

### Improvement Suggestions
List concrete, actionable suggestions for improving the code, such as:
- Better naming or code organization
- Missing tests or test coverage gaps
- Documentation that should be added
- Alternative approaches worth considering

### Confidence Score
Rate your confidence as **Low**, **Medium**, or **High** based on:
- **High** — You can clearly assess the change; the diff is self-contained.
- **Medium** — The change is understandable but you lack full project context.
- **Low** — The diff is too large, too fragmented, or domain-specific to assess well.

Explain briefly why you chose that rating."

# ── Call Claude ───────────────────────────────────────────────────────────────

info "Sending to Claude for review..."

if [[ "$USE_CLAUDE_CLI" == "true" ]]; then
  REVIEW=$(echo "$REVIEW_PROMPT" | claude --print 2>/dev/null) || die "Claude CLI failed"
else
  # Use Anthropic API directly via curl
  ESCAPED_PROMPT=$(echo "$REVIEW_PROMPT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")

  API_RESPONSE=$(curl -s -w "\n%{http_code}" \
    https://api.anthropic.com/v1/messages \
    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "{
      \"model\": \"${MODEL}\",
      \"max_tokens\": 4096,
      \"messages\": [{
        \"role\": \"user\",
        \"content\": ${ESCAPED_PROMPT}
      }]
    }")

  HTTP_CODE=$(echo "$API_RESPONSE" | tail -1)
  API_BODY=$(echo "$API_RESPONSE" | sed '$d')

  if [[ "$HTTP_CODE" != "200" ]]; then
    die "Anthropic API returned HTTP $HTTP_CODE: $API_BODY"
  fi

  REVIEW=$(echo "$API_BODY" | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
for block in data.get('content', []):
    if block.get('type') == 'text':
        print(block['text'])
" 2>/dev/null) || die "failed to parse API response"
fi

# ── Format Output ────────────────────────────────────────────────────────────

HEADER="# PR Review: ${PR_TITLE}

> **PR:** [#${PR_NUMBER}](${PR_URL}) | **Author:** ${PR_AUTHOR} | **Changes:** +${PR_ADDITIONS}/-${PR_DELETIONS} in ${PR_CHANGED} files
> **Reviewed by:** Claude Code PR Review Agent v${VERSION}
> **Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)

---

${REVIEW}"

if [[ "$FORMAT" == "json" ]]; then
  # Wrap in JSON
  OUTPUT_TEXT=$(python3 -c "
import json, sys
review = sys.stdin.read()
print(json.dumps({
    'pr_url': '${PR_URL}',
    'pr_number': ${PR_NUMBER},
    'repo': '${REPO}',
    'title': '${PR_TITLE}',
    'author': '${PR_AUTHOR}',
    'review': review,
    'version': '${VERSION}'
}, indent=2))
" <<< "$REVIEW")
else
  OUTPUT_TEXT="$HEADER"
fi

# ── Write Output ─────────────────────────────────────────────────────────────

if [[ -n "$OUTPUT" ]]; then
  echo "$OUTPUT_TEXT" > "$OUTPUT"
  echo "Review written to: $OUTPUT" >&2
else
  echo "$OUTPUT_TEXT"
fi
