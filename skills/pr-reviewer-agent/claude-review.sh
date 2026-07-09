#!/usr/bin/env bash
# claude-review.sh — PR Reviewer Agent for Claude Code
# Reviews GitHub PR diffs and posts structured Markdown feedback
# Usage: bash claude-review.sh --pr <pr-url>
#        bash claude-review.sh --pr https://github.com/owner/repo/pull/123

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
CLAUDE_API_KEY="${CLAUDE_API_KEY:-$OPENAI_API_KEY}"
MODEL="${MODEL:-claude-sonnet-4-20250514}"

# ─── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }
section() { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }

# ─── Help ───────────────────────────────────────────────────────────────────

usage() {
    cat << EOF
Usage: bash claude-review.sh --pr <pr-url> [options]

Review a GitHub PR diff and generate structured feedback.

Options:
  --pr <url>         GitHub PR URL (required)
  --model <name>     Claude model to use (default: claude-sonnet-4-20250514)
  --output <file>    Write review to file instead of stdout
  --json             Output raw JSON from Claude
  --help             Show this help

Examples:
  bash claude-review.sh --pr https://github.com/owner/repo/pull/123
  bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
  GITHUB_TOKEN=ghp_xxx CLAUDE_API_KEY=sk-xxx bash claude-review.sh --pr https://github.com/owner/repo/pull/456
EOF
    exit 0
}

# ─── Parse Arguments ────────────────────────────────────────────────────────

PR_URL=""
OUTPUT_FILE=""
OUTPUT_JSON=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --json) OUTPUT_JSON=true; shift ;;
        --help|-h) usage ;;
        *) error "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$PR_URL" ]; then
    error "PR URL is required. Use: --pr <url>"
    usage
fi

if [ -z "$GITHUB_TOKEN" ]; then
    error "GITHUB_TOKEN environment variable is not set"
    exit 1
fi

if [ -z "$CLAUDE_API_KEY" ]; then
    error "CLAUDE_API_KEY or OPENAI_API_KEY environment variable is not set"
    exit 1
fi

# ─── Parse PR URL ───────────────────────────────────────────────────────────

# Extract owner, repo, PR number from URL
# Supports: https://github.com/owner/repo/pull/123, github.com/owner/repo/pull/123
PR_INFO=$(echo "$PR_URL" | sed -E 's|.*github.com[:/]([^/]+)/([^/]+)/pull/([0-9]+).*|\1|\2|\3|')
OWNER=$(echo "$PR_INFO" | cut -d'|' -f1)
REPO=$(echo "$PR_INFO" | cut -d'|' -f2)
PR_NUMBER=$(echo "$PR_INFO" | cut -d'|' -f3)

if [ -z "$OWNER" ] || [ -z "$REPO" ] || [ -z "$PR_NUMBER" ]; then
    error "Could not parse PR URL: $PR_URL"
    error "Expected format: https://github.com/owner/repo/pull/123"
    exit 1
fi

info "Repository: $OWNER/$REPO"
info "PR #$PR_NUMBER"

# ─── Fetch PR Details ───────────────────────────────────────────────────────

section "Fetching PR details"

PR_DATA=$(curl -sf \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER" 2>/dev/null || true)

PR_TITLE=$(echo "$PR_DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('title', 'N/A'))
except: print('N/A')
" 2>/dev/null || echo "N/A")

PR_BODY=$(echo "$PR_DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    body = d.get('body', '') or ''
    print(body[:3000])
except: print('')
" 2>/dev/null || echo "")

PR_AUTHOR=$(echo "$PR_DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('user', {}).get('login', 'N/A'))
except: print('N/A')
" 2>/dev/null || echo "N/A")

info "Title: $PR_TITLE"
info "Author: $PR_AUTHOR"

# ─── Fetch PR Diff ──────────────────────────────────────────────────────────

section "Fetching diff"

DIFF=$(curl -sf \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER" 2>/dev/null || true)

if [ -z "$DIFF" ]; then
    # Fallback to the diff URL directly
    DIFF=$(curl -sfL \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://github.com/$OWNER/$REPO/pull/$PR_NUMBER.diff" 2>/dev/null || true)
fi

DIFF_SIZE=${#DIFF}
info "Diff size: ${DIFF_SIZE} bytes"

# Truncate diff if too large (Claude has token limits)
MAX_DIFF=80000
if [ ${#DIFF} -gt $MAX_DIFF ]; then
    warn "Diff is large (${DIFF_SIZE} bytes). Truncating to ${MAX_DIFF} bytes."
    DIFF="${DIFF:0:$MAX_DIFF}"
    DIFF="${DIFF}\n\n... [diff truncated due to size]"
fi

# ─── Fetch Changed Files ────────────────────────────────────────────────────

section "Fetching changed files"

FILES_JSON=$(curl -sf \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/files?per_page=100" 2>/dev/null || echo "[]")

CHANGED_FILES=$(echo "$FILES_JSON" | python3 -c "
import sys, json
try:
    files = json.load(sys.stdin)
    for f in files:
        status = f.get('status', 'modified')
        additions = f.get('additions', 0)
        deletions = f.get('deletions', 0)
        print(f'{status}: {f[\"filename\"]} (+{additions}/-{deletions})')
except: print('Could not parse file list')
" 2>/dev/null || echo "Could not parse")

info "Files changed:"
echo "$CHANGED_FILES"

ADDITIONS=$(echo "$FILES_JSON" | python3 -c "
import sys, json
try:
    files = json.load(sys.stdin)
    print(sum(f.get('additions', 0) for f in files))
except: print('0')
" 2>/dev/null || echo "0")

DELETIONS=$(echo "$FILES_JSON" | python3 -c "
import sys, json
try:
    files = json.load(sys.stdin)
    print(sum(f.get('deletions', 0) for f in files))
except: print('0')
" 2>/dev/null || echo "0")

TOTAL_FILES=$(echo "$FILES_JSON" | python3 -c "
import sys, json
try:
    files = json.load(sys.stdin)
    print(len(files))
except: print('0')
" 2>/dev/null || echo "0")

# ─── Build Prompt ───────────────────────────────────────────────────────────

section "Analyzing with Claude"

PROMPT=$(cat << PROMPTEOF
You are a senior software engineer conducting a thorough code review.

## PR Context
- **Repository:** $OWNER/$REPO
- **PR #$PR_NUMBER:** $PR_TITLE
- **Author:** $PR_AUTHOR
- **Files changed:** $TOTAL_FILES
- **Changes:** +$ADDITIONS / -$DELETIONS lines

## PR Description
$PR_BODY

## Changed Files
$CHANGED_FILES

## Diff
\`\`\`diff
$DIFF
\`\`\`

## Your Task
Review this pull request and provide structured feedback. Focus on:

1. **Summary** — 2-3 sentences explaining what this PR does and its overall quality
2. **Risks** — Security issues, performance problems, breaking changes, or logic errors
3. **Improvements** — Specific, actionable suggestions with code examples where possible
4. **Confidence** — How confident are you in your review? (Low / Medium / High)

### Guidelines
- Be constructive and specific. Bad: "This could be better." Good: "Consider using early return here to reduce nesting."
- Flag hardcoded secrets, SQL injection vectors, XSS vulnerabilities, and unsafe deserialization.
- Suggest test coverage for edge cases.
- If the PR is clean, say so. Don't fabricate issues.

Output format: Return ONLY valid JSON with keys: summary, risks (array), improvements (array), confidence (string).
PROMPTEOF
)

# ─── Call Claude API ────────────────────────────────────────────────────────

REQUEST_BODY=$(cat << JSONEOF
{
  "model": "$MODEL",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": $(echo "$PROMPT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
    }
  ]
}
JSONEOF
)

# Make API request
API_RESPONSE=$(curl -sf \
    -H "Content-Type: application/json" \
    -H "x-api-key: $CLAUDE_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d "$REQUEST_BODY" \
    "https://api.anthropic.com/v1/messages" 2>/dev/null || true)

if [ -z "$API_RESPONSE" ]; then
    error "Claude API request failed. Check your API key and network."
    exit 1
fi

# Extract the text response
REVIEW_TEXT=$(echo "$API_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for block in data.get('content', []):
        if block.get('type') == 'text':
            print(block['text'])
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null || echo "{\"error\": \"Failed to parse Claude response\"}")

if [ "$OUTPUT_JSON" = true ]; then
    echo "$API_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$API_RESPONSE"
    exit 0
fi

# ─── Format Output ──────────────────────────────────────────────────────────

section "Review Complete"

# Try to parse as JSON and format nicely
FORMATTED=$(echo "$REVIEW_TEXT" | python3 -c "
import sys, json

text = sys.stdin.read().strip()

# Try to extract JSON from the response
try:
    # Find JSON block (might be wrapped in markdown code fences)
    if '\`\`\`json' in text:
        text = text.split('\`\`\`json')[1].split('\`\`\`')[0].strip()
    elif '\`\`\`' in text:
        text = text.split('\`\`\`')[1].split('\`\`\`')[0].strip()

    review = json.loads(text)
    
    summary = review.get('summary', 'No summary provided.')
    risks = review.get('risks', [])
    improvements = review.get('improvements', [])
    confidence = review.get('confidence', 'Medium')
    
    # Build markdown
    lines = []
    lines.append('# Pull Request Review')
    lines.append('')
    lines.append(f'**PR:** {sys.argv[1] if len(sys.argv) > 1 else \"N/A\"}') 
    lines.append(f'**Confidence:** {confidence}')
    lines.append('')
    lines.append('## Summary')
    lines.append('')
    lines.append(summary)
    lines.append('')
    
    if risks:
        lines.append('## ⚠ Identified Risks')
        lines.append('')
        for r in risks:
            lines.append(f'- {r}')
        lines.append('')
    
    if improvements:
        lines.append('## 💡 Improvement Suggestions')
        lines.append('')
        for i, imp in enumerate(improvements, 1):
            lines.append(f'{i}. {imp}')
        lines.append('')
    
    lines.append('---')
    lines.append(f'_Generated by claude-review agent_')
    
    print('\\n'.join(lines))
except:
    # If not JSON, just print the raw text
    print(text)
" "$PR_URL" 2>/dev/null || echo "$REVIEW_TEXT")

echo -e "$FORMATTED"

# ─── Write output ───────────────────────────────────────────────────────────

if [ -n "$OUTPUT_FILE" ]; then
    echo -e "$FORMATTED" > "$OUTPUT_FILE"
    info "Review saved to: $OUTPUT_FILE"
fi

echo ""
info "Review complete. Confidence: $(echo "$FORMATTED" | grep -oP '(?<=\*\*Confidence:\*\* ).*' || echo 'N/A')"
