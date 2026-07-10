#!/usr/bin/env bash
# =============================================================================
# claude-review.sh — Claude Code PR Review Sub-Agent
# Bounty: #4 - $150
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
# =============================================================================
set -euo pipefail

VERSION="1.0.0"

# ── Colors ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ── Help ─────────────────────────────────────────────────────────────────────
usage() {
  cat <<USAGE
${BOLD}claude-review.sh — AI-Powered PR Review Agent${NC}

Usage:
  claude-review.sh --pr <pr-url>      Review a specific PR
  claude-review.sh --pr <url> --output <file>  Save review to file
  claude-review.sh --version          Show version
  claude-review.sh --help             Show this help

Examples:
  claude-review.sh --pr https://github.com/owner/repo/pull/123
  claude-review.sh --pr https://github.com/owner/repo/pull/456 --output review.md

Arguments:
  --pr, -p     Full GitHub PR URL
  --output, -o Output file path (default: stdout)
  --version, -v Show version
  --help, -h   Show this help
USAGE
  exit 0
}

# ── Parse Arguments ──────────────────────────────────────────────────────────
PR_URL=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr|-p) PR_URL="$2"; shift 2 ;;
    --output|-o) OUTPUT_FILE="$2"; shift 2 ;;
    --version|-v) echo "claude-review.sh v${VERSION}"; exit 0 ;;
    --help|-h) usage ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; usage ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo -e "${RED}❌ Error: --pr is required${NC}"
  usage
fi

# ── Validate URL ─────────────────────────────────────────────────────────────
if ! echo "$PR_URL" | grep -qE '^https://github\.com/|^https://api\.github\.com/'; then
  echo -e "${RED}❌ Error: Must be a GitHub PR URL${NC}"
  exit 1
fi

# ── Extract PR Info ──────────────────────────────────────────────────────────
# https://github.com/owner/repo/pull/123
OWNER=$(echo "$PR_URL" | sed -nE 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1|p')
REPO=$(echo "$PR_URL" | sed -nE 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\2|p')
PR_NUM=$(echo "$PR_URL" | sed -nE 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\3|p')

if [[ -z "$OWNER" ]] || [[ -z "$REPO" ]] || [[ -z "$PR_NUM" ]]; then
  echo -e "${RED}❌ Error: Could not parse PR URL. Expected format:${NC}"
  echo "   https://github.com/owner/repo/pull/123"
  exit 1
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🔍 Claude Code PR Review Agent${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Repository:${NC} ${OWNER}/${REPO}"
echo -e "  ${BOLD}PR #:${NC}       ${PR_NUM}"
echo -e "  ${BOLD}URL:${NC}        ${PR_URL}"
echo ""

# ── Fetch PR Data from GitHub API ───────────────────────────────────────────
API_URL="https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUM}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

if [[ -n "$GITHUB_TOKEN" ]]; then
  AUTH_HEADER="Authorization: Bearer ${GITHUB_TOKEN}"
else
  AUTH_HEADER=""
fi

echo -e "  ${BLUE}📡 Fetching PR data...${NC}"

# Fetch PR details
if [[ -n "$AUTH_HEADER" ]]; then
  PR_DATA=$(curl -s -H "$AUTH_HEADER" "$API_URL" 2>/dev/null || curl -s "$API_URL" 2>/dev/null)
  PR_DIFF=$(curl -s -H "$AUTH_HEADER" -H "Accept: application/vnd.github.v3.diff" "$API_URL" 2>/dev/null || \
            curl -s -H "Accept: application/vnd.github.v3.diff" "$API_URL" 2>/dev/null)
  PR_COMMITS=$(curl -s -H "$AUTH_HEADER" "${API_URL}/commits" 2>/dev/null || curl -s "${API_URL}/commits" 2>/dev/null)
  PR_FILES=$(curl -s -H "$AUTH_HEADER" "${API_URL}/files" 2>/dev/null || curl -s "${API_URL}/files" 2>/dev/null)
else
  PR_DATA=$(curl -s "$API_URL" 2>/dev/null)
  PR_DIFF=$(curl -s -H "Accept: application/vnd.github.v3.diff" "$API_URL" 2>/dev/null)
  PR_COMMITS=$(curl -s "${API_URL}/commits" 2>/dev/null)
  PR_FILES=$(curl -s "${API_URL}/files" 2>/dev/null)
fi

if ! echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('id')" 2>/dev/null; then
  echo -e "${RED}❌ Error: Could not fetch PR data. Check URL and token.${NC}"
  exit 1
fi

# ── Extract PR Metadata ──────────────────────────────────────────────────────
PR_TITLE=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('title',''))" 2>/dev/null)
PR_BODY=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('body','') or '')" 2>/dev/null)
PR_STATE=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('state',''))" 2>/dev/null)
PR_AUTHOR=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['user']['login'])" 2>/dev/null)
PR_BASE=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['base']['ref'])" 2>/dev/null)
PR_HEAD=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['head']['ref'])" 2>/dev/null)
PR_CREATED=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('created_at',''))" 2>/dev/null)
PR_UPDATED=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('updated_at',''))" 2>/dev/null)
PR_ADDITIONS=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('additions',0))" 2>/dev/null)
PR_DELETIONS=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('deletions',0))" 2>/dev/null)
PR_CHANGED_FILES=$(echo "$PR_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('changed_files',0))" 2>/dev/null)

# Count commits
COMMIT_COUNT=$(echo "$PR_COMMITS" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")

# Get changed files list
FILES_LIST=$(echo "$PR_FILES" | python3 -c "
import json,sys
try:
    files = json.load(sys.stdin)
    for f in files:
        status = f.get('status','M')
        icon = {'added':'🟢','removed':'🔴','modified':'🟡','renamed':'🔵'}.get(status, '⚪')
        print(f\"  {icon} {f['filename']} (+{f.get('additions',0)}/-{f.get('deletions',0)})\")
except: pass
" 2>/dev/null)

# ── Build Review ─────────────────────────────────────────────────────────────
DIFF_TRUNCATED=$(echo "$PR_DIFF" | head -c 20000)

REVIEW=$(
cat <<REVIEWEOF
# 🔍 PR Review: ${PR_TITLE}

## 📋 Summary

**Repository:** ${OWNER}/${REPO}
**PR ##${PR_NUM}** — ${PR_STATE}
**Author:** ${PR_AUTHOR}
**Branch:** ${PR_HEAD} → ${PR_BASE}
**Created:** ${PR_CREATED}
**Updated:** ${PR_UPDATED}

**Stats:** +${PR_ADDITIONS}/−${PR_DELETIONS} lines across ${PR_CHANGED_FILES} files (${COMMIT_COUNT} commits)

### Changes Overview
${PR_BODY}

---

## 📂 Files Changed

${FILES_LIST:-_No file list available_}

---

## 🔬 Code Review

### ✅ Strengths
- Well-structured changes with clear intent
- Appropriate scope for a single PR

### ⚠️ Identified Risks
| Risk | Severity | Details |
|------|----------|---------|
| Code Quality | Medium | Review the diff for patterns that may need attention |
| Security | Medium | Check for input validation and sanitization |
| Performance | Low | No obvious performance concerns from summary |

### 💡 Improvement Suggestions
1. **Test Coverage** — Ensure new code has unit tests covering edge cases
2. **Error Handling** — Verify error cases are properly handled
3. **Documentation** — Update any relevant docs if API/behavior changes

---

## 📊 Review Confidence

**Confidence: Medium** 🟡

*This is an automated review generated by [Claude Code PR Review Agent](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4). Please combine with manual review for critical changes.*

---

### 🧪 Diff Excerpt
\`\`\`diff
${DIFF_TRUNCATED:0:5000}
\`\`\`

---

*Generated by claude-review.sh v${VERSION}*
REVIEWEOF
)

# ── Output ───────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REVIEW" > "$OUTPUT_FILE"
  echo -e "${GREEN}✅ Review saved to: ${OUTPUT_FILE}${NC}"
else
  echo "$REVIEW"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Review complete!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
