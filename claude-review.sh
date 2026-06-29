#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# claude-review.sh — PR Reviewer sub-agent with structured markdown output
#
# Usage:
#   ./claude-review.sh --pr https://github.com/owner/repo/pull/123
#   ./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post
#
# Environment:
#   GITHUB_TOKEN       — Required. GitHub personal access token with repo scope.
#   ANTHROPIC_API_KEY  — Optional. Falls back to diff-only analysis if unset.
#
# Flags:
#   --pr <url>  GitHub PR URL to review
#   --post      Post the review as a comment on the PR
#   --help      Show this help
# ============================================================

VERSION="1.0.0"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()   { err "$*"; exit 1; }

usage() {
  cat <<EOF
Usage: $0 --pr <pr-url> [--post] [--help]

Review a GitHub PR using Claude AI and produce structured markdown output.

Required:
  --pr <url>     Full GitHub pull-request URL

Optional:
  --post         Post the review as a comment on the PR
  --help         Show this help message

Environment:
  GITHUB_TOKEN       (required) GitHub personal access token
  ANTHROPIC_API_KEY  (optional) Anthropic API key for Claude analysis
EOF
  exit 0
}

# Parse arguments
PR_URL=""
POST_COMMENT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)      PR_URL="$2"; shift 2 ;;
    --post)    POST_COMMENT=true; shift ;;
    --help)    usage ;;
    *)         die "Unknown option: $1. Use --help for usage." ;;
  esac
done

[[ -z "$PR_URL" ]] && die "Missing --pr argument."

if ! command -v curl &>/dev/null; then die "curl is required."; fi
if ! command -v jq &>/dev/null; then die "jq is required (apt install jq)."; fi

# Parse PR URL
if [[ $PR_URL =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"
else
  die "Could not parse PR URL. Expected: https://github.com/owner/repo/pull/123"
fi

GH_API="https://api.github.com"
PR_API="$GH_API/repos/$OWNER/$REPO/pulls/$PR_NUMBER"
info "Reviewing PR #$PR_NUMBER — $OWNER/$REPO"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then die "GITHUB_TOKEN not set."; fi

# Fetch PR metadata
info "Fetching PR metadata..."
PR_JSON=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" "$PR_API")
PR_TITLE=$(echo "$PR_JSON" | jq -r '.title // empty')
PR_BODY=$(echo "$PR_JSON" | jq -r '.body // "[no description]"')
PR_AUTHOR=$(echo "$PR_JSON" | jq -r '.user.login // "unknown"')
PR_STATE=$(echo "$PR_JSON" | jq -r '.state // "unknown"')
PR_BASE=$(echo "$PR_JSON" | jq -r '.base.ref // "unknown"')
PR_HEAD=$(echo "$PR_JSON" | jq -r '.head.ref // "unknown"')
PR_CREATED=$(echo "$PR_JSON" | jq -r '.created_at // "unknown"')
PR_CHANGED_FILES=$(echo "$PR_JSON" | jq -r '.changed_files // 0')
PR_ADDITIONS=$(echo "$PR_JSON" | jq -r '.additions // 0')
PR_DELETIONS=$(echo "$PR_JSON" | jq -r '.deletions // 0')
[[ -z "$PR_TITLE" ]] && die "PR not found or token lacks access."
ok "PR: $PR_TITLE (by $PR_AUTHOR, $PR_STATE)"
info "Base: $PR_BASE <- Head: $PR_HEAD"
info "Files: $PR_CHANGED_FILES | +$PR_ADDITIONS / -$PR_DELETIONS"

# Fetch PR diff
info "Fetching PR diff..."
PR_DIFF=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3.diff" "$PR_API")
DIFF_SIZE=${#PR_DIFF}
info "Diff size: $DIFF_SIZE bytes"
[[ "$DIFF_SIZE" -eq 0 ]] && die "PR diff is empty."

# Fetch commit messages
info "Fetching commit messages..."
COMMITS_JSON=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" "$PR_API/commits")
COMMIT_MSGS=$(echo "$COMMITS_JSON" | jq -r '.[].commit.message // empty' | head -20)

# --- review_diff_only: stat-based review ---
review_diff_only() {
  info "Performing diff-only review..."
  TOTAL_LINES=$(echo "$PR_DIFF" | wc -l)
  ADDED_LINES=$(echo "$PR_DIFF" | grep -c '^+[^+]' || true)
  REMOVED_LINES=$(echo "$PR_DIFF" | grep -c '^-[^-]' || true)
  FILES_CHANGED=$(echo "$PR_DIFF" | grep -c '^+++ ' || true)
  LANGUAGES=$(echo "$PR_DIFF" | grep '^+++ ' | sed 's/.*\.//' | sort -u | tr '\n' ', ' | sed 's/,$//')
  [[ -z "$LANGUAGES" ]] && LANGUAGES="unknown"
  HAS_TESTS="No";   echo "$PR_DIFF" | grep -qiE '(test|spec|jest|vitest|pytest|unittest)' && HAS_TESTS="Yes"
  HAS_ERROR="No";   echo "$PR_DIFF" | grep -qiE '(catch|try|error|panic|recover)' && HAS_ERROR="Yes"
  HAS_SEC="No";     echo "$PR_DIFF" | grep -qiE '(token|password|secret|auth|permission|sanitize|escape)' && HAS_SEC="Yes"
  HAS_BREAK="No";   echo "$PR_DIFF" | grep -qiE '(BREAKING CHANGE|deprecated|migration|breaking)' && HAS_BREAK="Yes"
  RISK_POINTS=0
  [[ "$TOTAL_LINES" -gt 500 ]]  && RISK_POINTS=$((RISK_POINTS + 2))
  [[ "$FILES_CHANGED" -gt 10 ]] && RISK_POINTS=$((RISK_POINTS + 2))
  [[ "$HAS_BREAK" != "No" ]]    && RISK_POINTS=$((RISK_POINTS + 3))
  [[ "$HAS_TESTS" == "No" ]]    && RISK_POINTS=$((RISK_POINTS + 1))
  if   [[ "$RISK_POINTS" -le 2 ]]; then RISK_LEVEL="Low"
  elif [[ "$RISK_POINTS" -le 4 ]]; then RISK_LEVEL="Medium"
  else RISK_LEVEL="High"; fi
  CONFIDENCE=75
  [[ "$HAS_TESTS" == "Yes" ]] && CONFIDENCE=$((CONFIDENCE + 10))
  [[ "$HAS_SEC" == "Yes" ]]   && CONFIDENCE=$((CONFIDENCE + 5))
  [[ "$RISK_POINTS" -le 2 ]]  && CONFIDENCE=$((CONFIDENCE + 10))
  [[ "$RISK_POINTS" -ge 5 ]]  && CONFIDENCE=$((CONFIDENCE - 10))
  [[ "$CONFIDENCE" -gt 95 ]]  && CONFIDENCE=95
  [[ "$CONFIDENCE" -lt 30 ]]  && CONFIDENCE=30

  REVIEW="## Summary

This PR (**$PR_TITLE**) by **$PR_AUTHOR** modifies **$FILES_CHANGED files** across **$TOTAL_LINES lines** ($ADDED_LINES added, $REMOVED_LINES removed).

The changes span **${PR_CHANGED_FILES} file(s)** ($PR_ADDITIONS additions, $PR_DELETIONS deletions) on branch \`$PR_HEAD\` to \`$PR_BASE\$.

**Languages detected:** $LANGUAGES

### Commit Overview
\`\`\`
$COMMIT_MSGS
\`\`\`

---

## Risks

| Risk Factor | Status |
|-------------|--------|
| Scope | $TOTAL_LINES lines across $FILES_CHANGED files |
| Breaking changes | $HAS_BREAK |
| Security-sensitive patterns | $HAS_SEC |
| Error handling | $HAS_ERROR |
| Tests included | $HAS_TESTS |

**Overall Risk Level:** $RISK_LEVEL ($RISK_POINTS/10 risk points)

---

## Improvements

- [ ] Review for edge cases and error handling
- [ ] Check that all new functions/types are documented
- [ ] Verify the diff doesn't introduce dead code or commented-out blocks
- [ ] Ensure naming consistency with existing codebase
- [ ] Look for any hardcoded values that should be configurable

---

## Confidence

**Confidence Score: ${CONFIDENCE}%**

This review is based on statistical diff analysis. For a deeper, AI-powered review, set \`ANTHROPIC_API_KEY\` and re-run.

---

*Generated by claude-review.sh v$VERSION — diff-only analysis mode*"
}

# --- review_with_claude: AI-powered review ---
review_with_claude() {
  info "Calling Claude API for AI-powered review..."
  MAX_DIFF_CHARS=80000
  TRIMMED_DIFF="$PR_DIFF"
  DIFF_TRUNCATED=false
  if [[ ${#TRIMMED_DIFF} -gt $MAX_DIFF_CHARS ]]; then
    TRIMMED_DIFF="${TRIMMED_DIFF:0:$MAX_DIFF_CHARS}"
    DIFF_TRUNCATED=true
  fi

  PROMPT="You are an expert code reviewer assisting with a GitHub pull request.

Analyze the following PR and produce a structured review in markdown with these sections:

1. **Summary** - What does this PR do? High-level overview (2-4 sentences).
2. **Risks** - Security concerns, breaking changes, performance implications, regressions.
3. **Improvements** - Specific, actionable suggestions (code quality, readability, edge cases).
4. **Confidence** - A confidence percentage (0-100%) and brief justification.

PR Title: $PR_TITLE
PR Author: $PR_AUTHOR
Base: $PR_BASE <- Head: $PR_HEAD
Files Changed: $PR_CHANGED_FILES | +$PR_ADDITIONS / -$PR_DELETIONS

PR Description:
$PR_BODY

Commits:
$COMMIT_MSGS

$([ "$DIFF_TRUNCATED" = true ] && echo "Note: diff truncated to fit context.") 

Diff:
\`\`\`diff
$TRIMMED_DIFF
\`\`\`

Provide structured markdown review now. Be specific and cite line ranges."
  
  CLAUDE_API="https://api.anthropic.com/v1/messages"
  PAYLOAD=$(jq -n --arg model "claude-sonnet-4-20250514" --arg prompt "$PROMPT" '{
    model: $model,
    max_tokens: 4096,
    messages: [{ role: "user", content: $prompt }]
  }')
  
  CLAUDE_RESP=$(curl -sS -w "\n%{http_code}" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d "$PAYLOAD" "$CLAUDE_API")
  
  HTTP_CODE=$(echo "$CLAUDE_RESP" | tail -1)
  BODY=$(echo "$CLAUDE_RESP" | sed '$d')
  
  if [[ "$HTTP_CODE" != "200" ]]; then
    warn "Claude API returned HTTP $HTTP_CODE — falling back to diff-only analysis."
    review_diff_only
    return
  fi
  
  REVIEW=$(echo "$BODY" | jq -r '.content[0].text // empty')
  if [[ -z "$REVIEW" ]]; then
    warn "Claude returned empty — falling back to diff-only."
    review_diff_only
    return
  fi
  REVIEW="$REVIEW

---

*Generated by claude-review.sh v$VERSION — AI-powered by Claude*"
}

# Decide reviewer
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  review_with_claude
else
  warn "ANTHROPIC_API_KEY not set — using diff-only analysis."
  info "Set ANTHROPIC_API_KEY for AI-powered review."
  review_diff_only
fi

# Output
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  PR Review - $OWNER/$REPO #$PR_NUMBER${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "$REVIEW"
echo ""

# Post comment
if $POST_COMMENT; then
  info "Posting review comment on PR #$PR_NUMBER..."
  ESCAPED=$(echo "$REVIEW" | jq -Rs .)
  POST_RESP=$(curl -sS -w "\n%{http_code}" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "{\"body\": $ESCAPED}" \
    "$GH_API/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments")
  
  POST_CODE=$(echo "$POST_RESP" | tail -1)
  POST_BODY=$(echo "$POST_RESP" | sed '$d')
  
  if [[ "$POST_CODE" = "201" ]]; then
    COMMENT_URL=$(echo "$POST_BODY" | jq -r '.html_url // "created"')
    ok "Comment posted: $COMMENT_URL"
  else
    err "Failed to post comment (HTTP $POST_CODE)"
    err "Response: $(echo "$POST_BODY" | jq -r '.message // "unknown"' 2>/dev/null)"
  fi
fi

ok "Review complete."
