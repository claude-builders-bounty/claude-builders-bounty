#!/usr/bin/env bash
# claude-review — Review a GitHub PR and output structured Markdown analysis
#
# Usage:
#   bash claude-review.sh --pr https://github.com/owner/repo/pull/123
#   bash claude-review.sh --pr owner/repo#123
#   bash claude-review.sh --pr 123  (uses current repo)
#
# Requires: gh CLI (authenticated), claude CLI (Claude Code)
# Optional: ANTHROPIC_API_KEY env var for direct API usage

set -euo pipefail

PR_URL=""

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash claude-review.sh --pr <url|owner/repo#N|N>"
      echo ""
      echo "  --pr   PR URL, owner/repo#N, or just the number (for current repo)"
      echo ""
      echo "Requires: gh CLI (authenticated)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required. Run with --help for usage." >&2
  exit 1
fi

# --- Resolve PR reference ---
# Handle different formats: URL, owner/repo#N, just N
if [[ "$PR_URL" =~ ^https://github.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUM="${BASH_REMATCH[2]}"
elif [[ "$PR_URL" =~ ^([^/]+/[^#]+)#([0-9]+)$ ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUM="${BASH_REMATCH[2]}"
elif [[ "$PR_URL" =~ ^[0-9]+$ ]]; then
  REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo "")
  PR_NUM="$PR_URL"
  if [[ -z "$REPO" ]]; then
    echo "Error: Could not detect current repo. Use full URL or owner/repo#N format." >&2
    exit 1
  fi
else
  echo "Error: Unrecognized PR format: $PR_URL" >&2
  echo "Expected: https://github.com/owner/repo/pull/N, owner/repo#N, or N" >&2
  exit 1
fi

echo "Reviewing: ${REPO}#${PR_NUM}" >&2

# --- Fetch PR metadata ---
PR_DATA=$(gh pr view "$PR_NUM" --repo "$REPO" --json title,body,author,additions,deletions,files,commits 2>&1)
if [[ $? -ne 0 ]]; then
  echo "Error: Failed to fetch PR data. Is gh authenticated?" >&2
  echo "$PR_DATA" >&2
  exit 1
fi

PR_TITLE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
PR_AUTHOR=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['author']['login'])")
PR_ADDITIONS=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['additions'])")
PR_DELETIONS=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['deletions'])")
PR_FILES=$(echo "$PR_DATA" | python3 -c "import sys,json; files=json.load(sys.stdin)['files']; [print(f['path']) for f in files]")
PR_COMMITS=$(echo "$PR_DATA" | python3 -c "import sys,json; commits=json.load(sys.stdin)['commits']; [print(c['messageHeadline']) for c in commits]")

# --- Fetch diff ---
DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "Error: Failed to fetch PR diff." >&2
  exit 1
fi

# Truncate very large diffs to avoid token limits
DIFF_LINES=$(echo "$DIFF" | wc -l)
if [[ "$DIFF_LINES" -gt 500 ]]; then
  DIFF=$(echo "$DIFF" | head -500)
  DIFF="${DIFF}

... (diff truncated at 500 lines, ${DIFF_LINES} total)"
fi

# --- Build the review prompt ---
PROMPT=$(cat <<PROMPT_EOF
You are a senior code reviewer. Analyze this GitHub pull request and produce a structured review.

## PR Metadata
- **Title**: ${PR_TITLE}
- **Author**: ${PR_AUTHOR}
- **Size**: +${PR_ADDITIONS} / -${PR_DELETIONS} lines
- **Files changed**: $(echo "$PR_FILES" | wc -l | tr -d ' ')

### Files
${PR_FILES}

### Commits
${PR_COMMITS}

## Diff
\`\`\`diff
${DIFF}
\`\`\`

## Instructions

Produce EXACTLY this Markdown structure:

### Summary
2-3 sentences describing what this PR does and why.

### Identified Risks
- List each risk with severity (🔴 High / 🟡 Medium / 🟢 Low)
- If no risks: "No significant risks identified."

### Improvement Suggestions
- Actionable, specific suggestions with code references
- If none: "No suggestions — this PR looks solid."

### Confidence Score
State one of: **Low** / **Medium** / **High**
With a one-line justification.

Be concise. Focus on what matters. Skip praise.
PROMPT_EOF
)

# --- Call Claude ---
# Try claude CLI first (Claude Code), fall back to API
if command -v claude &>/dev/null; then
  REVIEW=$(echo "$PROMPT" | claude -p --output-format text 2>/dev/null)
elif [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  # Direct API call
  ESCAPED_PROMPT=$(echo "$PROMPT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
  REVIEW=$(curl -s https://api.anthropic.com/v1/messages \
    -H "content-type: application/json" \
    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
    -H "anthropic-version: 2023-06-01" \
    -d "{
      \"model\": \"claude-sonnet-4-20250514\",
      \"max_tokens\": 2048,
      \"messages\": [{\"role\": \"user\", \"content\": ${ESCAPED_PROMPT}}]
    }" | python3 -c "import sys,json; print(json.load(sys.stdin)['content'][0]['text'])")
else
  echo "Error: Neither 'claude' CLI nor ANTHROPIC_API_KEY found." >&2
  echo "Install Claude Code or set ANTHROPIC_API_KEY." >&2
  exit 1
fi

# --- Output ---
cat <<OUTPUT
# PR Review: ${REPO}#${PR_NUM}

> **${PR_TITLE}** by @${PR_AUTHOR}
> +${PR_ADDITIONS} / -${PR_DELETIONS} lines across $(echo "$PR_FILES" | wc -l | tr -d ' ') files

${REVIEW}

---
*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) on $(date '+%Y-%m-%d %H:%M UTC')*
OUTPUT
