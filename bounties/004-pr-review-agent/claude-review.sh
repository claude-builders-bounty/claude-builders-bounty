#!/usr/bin/env bash
# claude-review — PR Review Agent for Claude Code
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
# Bounty: Claude Builders #4 ($150)

set -euo pipefail

# Configuration
DEFAULT_MODEL="claude-sonnet-4-20250514"
CONFIDENCE_LEVELS=("Low" "Medium" "High")
REVIEW_DIR="${HOME}/.claude-review"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

usage() {
    cat <<EOF
Usage: claude-review --pr <PR_URL> [--model <MODEL>] [--output <FILE>]

Options:
  --pr <URL>       GitHub PR URL (required)
  --model <MODEL>  Claude model to use (default: ${DEFAULT_MODEL})
  --output <FILE>  Save review to file instead of stdout
  --help           Show this help

Example:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
EOF
    exit 0
}

# Parse arguments
PR_URL=""
MODEL="${DEFAULT_MODEL}"
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "${PR_URL}" ]]; then
    echo -e "${RED}Error: --pr is required${NC}"
    usage
fi

# Validate PR URL format: https://github.com/owner/repo/pull/NNN
if ! echo "${PR_URL}" | grep -qE '^https://github\.com/[^/]+/[^/]+/pull/[0-9]+$'; then
    echo -e "${RED}Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/NNN${NC}"
    exit 1
fi

OWNER=$(echo "${PR_URL}" | cut -d'/' -f4)
REPO=$(echo "${PR_URL}" | cut -d'/' -f5)
PR_NUM=$(echo "${PR_URL}" | cut -d'/' -f7)

echo -e "${GREEN}Analyzing PR: ${OWNER}/${REPO}#${PR_NUM}${NC}"

# Create temp directory
TMPDIR=$(mktemp -d)
trap "rm -rf ${TMPDIR}" EXIT

# Fetch PR diff using GitHub API
DIFF_URL="https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}"
PR_DETAILS=$(curl -s "${DIFF_URL}" || echo '{"error":"Failed to fetch PR"}')

# Fetch the actual diff
DIFF_CONTENT=$(curl -s -H "Accept: application/vnd.github.v3.diff" "${DIFF_URL}" || echo "")

if [[ -z "${DIFF_CONTENT}" ]]; then
    echo -e "${RED}Error: Could not fetch diff for ${PR_URL}${NC}"
    exit 1
fi

# Extract PR title and description
PR_TITLE=$(echo "${PR_DETAILS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','Unknown'))" 2>/dev/null || echo "Unknown")
PR_BODY=$(echo "${PR_DETAILS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('body','')[:500])" 2>/dev/null || echo "")

# Write diff to temp file for analysis
DIFF_FILE="${TMPDIR}/diff.patch"
echo "${DIFF_CONTENT}" > "${DIFF_FILE}"

DIFF_STATS=$(echo "${DIFF_CONTENT}" | grep -E '^\+\+\+ |^--- |^@@' | head -50)
FILES_CHANGED=$(echo "${DIFF_CONTENT}" | grep -cE '^--- a/' || echo "0")
ADDITIONS=$(echo "${DIFF_CONTENT}" | grep -cE '^\+' || echo "0")
DELETIONS=$(echo "${DIFF_CONTENT}" | grep -cE '^\-' || echo "0")

# Generate structured review prompt for Claude
REVIEW_PROMPT=$(cat <<PROMPT
You are a senior code reviewer. Analyze this GitHub pull request and produce a structured Markdown review.

PR: ${PR_TITLE}
Description: ${PR_BODY}

## Diff Statistics
- Files changed: ${FILES_CHANGED}
- Lines added: ${ADDITIONS}
- Lines deleted: ${DELETIONS}

## Diff Summary (first 50 lines)
\`\`\`
${DIFF_STATS}
\`\`\`

## Full Diff
\`\`\`diff
${DIFF_CONTENT}
\`\`\`

## Instructions

Produce a review with these sections in Markdown:

### Summary
2-3 sentences describing what this PR does. Be specific — mention the files changed and the overall goal.

### Changed Files
List each file and what changed in it (one sentence per file).

### Identified Risks
List potential risks (security, performance, breaking changes, edge cases). Use bullet points. If none are clear, state that.

### Improvement Suggestions
Actionable suggestions for improvement. Consider: error handling, tests, code clarity, performance, naming.

### Confidence Score
One of: Low / Medium / High — based on how well you understand the full impact of the changes.

Keep your response CONCISE. Each bullet should be one line.
PROMPT
)

# Call Claude Code or Claude API
REVIEW_CONTENT=""
if command -v claude &>/dev/null; then
    echo -e "${YELLOW}Using Claude Code CLI...${NC}"
    REVIEW_CONTENT=$(echo "${REVIEW_PROMPT}" | claude -p --model "${MODEL}" 2>/dev/null || echo "")
fi

# Fallback: if Claude CLI is not available, use curl to Anthropic API
if [[ -z "${REVIEW_CONTENT}" ]]; then
    echo -e "${YELLOW}Falling back to Anthropic API...${NC}"
    ANTHROPIC_KEY="${ANTHROPIC_API_KEY:-}"
    if [[ -z "${ANTHROPIC_KEY}" ]]; then
        echo -e "${RED}Error: No Claude CLI or ANTHROPIC_API_KEY available${NC}"
        echo -e "${YELLOW}Set ANTHROPIC_API_KEY environment variable or install Claude Code CLI.${NC}"
        exit 1
    fi

    REVIEW_RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: ${ANTHROPIC_KEY}" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "{
            "model": "${MODEL}",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": $(echo "${REVIEW_PROMPT}" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}]
        }" 2>/dev/null)

    REVIEW_CONTENT=$(echo "${REVIEW_RESPONSE}" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print(d['content'][0]['text'])
except:
    print('Error: Could not parse API response')
" 2>/dev/null)
fi

# Format final output
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
FINAL_REVIEW=$(cat <<EOF
# 🔍 PR Review: ${OWNER}/${REPO}#${PR_NUM}

**PR**: [${PR_TITLE}](${PR_URL})  
**Reviewed**: ${TIMESTAMP}  
**Reviewer**: Claude Code (${MODEL})

---

${REVIEW_CONTENT}

---

*🤖 This review was generated by [claude-review](https://github.com/ouzegba-lgtm/claude-review) — a Claude Code sub-agent for automated PR analysis.*
EOF
)

# Output
if [[ -n "${OUTPUT}" ]]; then
    mkdir -p "$(dirname "${OUTPUT}")"
    echo "${FINAL_REVIEW}" > "${OUTPUT}"
    echo -e "${GREEN}Review saved to: ${OUTPUT}${NC}"
else
    echo "${FINAL_REVIEW}"
fi

echo ""
echo -e "${GREEN}✅ Review complete!${NC}"
