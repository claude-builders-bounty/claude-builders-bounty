#!/bin/bash
#
# pr-review.sh — PR Review Agent
# Analyzes a PR diff and outputs a structured review
# Usage: pr-review.sh OWNER REPO PR_NUMBER [--dry-run] [--verbose]
#

set -euo pipefail

# --- Config ---
OWNER=""
REPO=""
PR_NUM=""
DRY_RUN=0
VERBOSE=0
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    -h|--help)
      echo "Usage: $0 OWNER_REPO PR_NUMBER [--dry-run] [--verbose]"
      echo "   or: $0 https://github.com/OWNER/REPO/pull/PR_NUM [--dry-run] [--verbose]"
      exit 0
      ;;
    http*://github.com/*/pull/*)
      # Parse URL like https://github.com/owner/repo/pull/123
      URL_PATH=$(echo "$1" | sed 's|https://github.com/||')
      OWNER=$(echo "$URL_PATH" | cut -d/ -f1)
      REPO=$(echo "$URL_PATH" | cut -d/ -f2)
      PR_NUM=$(echo "$URL_PATH" | grep -oP 'pull/\K\d+')
      shift
      ;;
    */*)
      # owner/repo format (single arg with slash)
      if [[ -z "$OWNER" ]]; then
        OWNER=$(echo "$1" | cut -d/ -f1)
        REPO=$(echo "$1" | cut -d/ -f2)
      elif [[ -z "$PR_NUM" ]]; then
        PR_NUM="$1"
      fi
      shift
      ;;
    *)
      # Standalone positional args: owner repo pr_num
      if [[ -z "$OWNER" ]]; then
        OWNER="$1"
      elif [[ -z "$REPO" ]]; then
        REPO="$1"
      elif [[ -z "$PR_NUM" ]]; then
        PR_NUM="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$OWNER" || -z "$REPO" || -z "$PR_NUM" ]]; then
  echo "ERROR: Usage: $0 OWNER REPO PR_NUMBER"
  exit 1
fi

# --- Auth ---
GH_CMD="gh api"
if [[ -n "$GITHUB_TOKEN" ]]; then
  GH_CMD="gh api -H 'Authorization: token $GITHUB_TOKEN'"
fi

# --- Colors (for terminal) ---
if [[ -t 1 ]] && [[ $DRY_RUN -eq 1 || -z "$GITHUB_TOKEN" ]]; then
  BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; CYAN="\033[36m"; RESET="\033[0m"
else
  BOLD=""; GREEN=""; YELLOW=""; RED=""; CYAN=""; RESET=""
fi

# --- Fetch PR data ---
echo "📡 Fetching PR ${OWNER}/${REPO}#${PR_NUM}..." >&2

PR_JSON=$($GH_CMD "repos/${OWNER}/${REPO}/pulls/${PR_NUM}" 2>/dev/null) || {
  echo "ERROR: Failed to fetch PR. Check repo/name and PR number."
  exit 1
}

PR_TITLE=$(echo "$PR_JSON" | jq -r '.title')
PR_BODY=$(echo "$PR_JSON" | jq -r '.body // ""')
PR_AUTHOR=$(echo "$PR_JSON" | jq -r '.user.login')
PR_CHANGED_FILES=$(echo "$PR_JSON" | jq -r '.changed_files')
PR_ADDITIONS=$(echo "$PR_JSON" | jq -r '.additions')
PR_DELETIONS=$(echo "$PR_JSON" | jq -r '.deletions')

# --- Fetch diff ---
DIFF=$($GH_CMD "repos/${OWNER}/${REPO}/pulls/${PR_NUM}" \
  -H "Accept: application/vnd.github.v3.diff" 2>/dev/null) || {
  echo "ERROR: Failed to fetch diff."
  exit 1
}

# --- Analyze diff ---
ANALYSIS=""
RISKS=""
SUGGESTIONS=""
STRENGTHS=""
FILE_DETAILS=""
RISK_COUNT=0
SUGGESTION_COUNT=0
STRENGTH_COUNT=0

# Check for security patterns
SECURITY_ISSUES=()

# SQL injection patterns
SQL_PATTERNS=$(echo "$DIFF" | grep -iE "(SELECT|INSERT|UPDATE|DELETE).*\+.*\$" | grep -ivE "(prepared|parameter|bind)" || true)
if [[ -n "$SQL_PATTERNS" ]]; then
  SECURITY_ISSUES+=("🔴 **SQL Injection Risk**: Found raw SQL query construction without parameterized bindings")
fi

# XSS patterns
XSS_PATTERNS=$(echo "$DIFF" | grep -iE "(innerHTML|document\.write|eval\(|v-html)" || true)
if [[ -n "$XSS_PATTERNS" ]]; then
  SECURITY_ISSUES+=("🟡 **XSS Risk**: Direct DOM manipulation or eval() usage detected")
fi

# Hardcoded secrets
SECRET_PATTERNS=$(echo "$DIFF" | grep -iE '(\+\s*"[A-Za-z0-9]{20,}"|password\s*=\s*"|secret\s*=\s*"|api_key\s*=\s*")' || true)
if [[ -n "$SECRET_PATTERNS" ]]; then
  SECURITY_ISSUES+=("🔴 **Hardcoded Secret**: Possible hardcoded password/API key detected")
fi

# Input validation check
NEW_ENDPOINTS=$(echo "$DIFF" | grep -iE "^\+.*(app\.(get|post|put|delete)|router\.(get|post|put|delete))" || true)
VALIDATION_CHECK=$(echo "$DIFF" | grep -iE "(validate|schema|zod|joi|express-validator)" || true)
if [[ -n "$NEW_ENDPOINTS" && -z "$VALIDATION_CHECK" ]]; then
  SECURITY_ISSUES+=("🟡 **Missing Input Validation**: New endpoint(s) added without request validation")
fi

for issue in "${SECURITY_ISSUES[@]}"; do
  RISKS="${RISKS}- ${issue}\n"
  ((RISK_COUNT++)) || true
done

# Complexity check
ADDED_LINES=$(echo "$DIFF" | grep -c "^+" || true)
DELETED_LINES=$(echo "$DIFF" | grep -c "^-" || true)
TOTAL_CHANGES=$((ADDED_LINES + DELETED_LINES))

if [[ $TOTAL_CHANGES -gt 500 ]]; then
  RISKS="${RISKS}- 🟡 **Large PR**: ${TOTAL_CHANGES} lines changed — consider splitting\n"
  ((RISK_COUNT++)) || true
elif [[ $TOTAL_CHANGES -gt 200 ]]; then
  RISKS="${RISKS}- 🟡 **Medium-large PR**: ${TOTAL_CHANGES} lines — review carefully\n"
  ((RISK_COUNT++)) || true
fi

# Test coverage
TEST_FILES=$(echo "$DIFF" | grep -cE "^\+\+\+ b/.*(\.test\.|\.spec\.|__tests__/)" || true)
SRC_FILES=$(echo "$DIFF" | grep -cE '^+++ b/.*.(js|ts|py|go|java)$' | grep -cvE "(test.|spec.|__tests__)" || echo 0)

if [[ $SRC_FILES -gt 0 && $TEST_FILES -eq 0 ]]; then
  SUGGESTIONS="${SUGGESTIONS}- Add unit tests for the changed source files (${SRC_FILES} files modified, 0 test files)\n"
  ((SUGGESTION_COUNT++)) || true
fi

# Check for TODO/FIXME/HACK comments
TODO_COUNT=$(echo "$DIFF" | grep -ciE "^\+.*//\s*(TODO|FIXME|HACK|XXX)" || true)
if [[ $TODO_COUNT -gt 0 ]]; then
  SUGGESTIONS="${SUGGESTIONS}- ${TODO_COUNT} TODO/FIXME comments found — consider creating follow-up issues\n"
  ((SUGGESTION_COUNT++)) || true
fi

# Check for console.log/debug left in
DEBUG_LOGS=$(echo "$DIFF" | grep -iE '^\+.*console\.(log|debug|warn)' || true)
if [[ -n "$DEBUG_LOGS" ]]; then
  SUGGESTIONS="${SUGGESTIONS}- Remove debug console.log/console.debug statements before merge\n"
  ((SUGGESTION_COUNT++)) || true
fi

# Detect strengths
# Has descriptive PR title?
if [[ ${#PR_TITLE} -ge 10 ]]; then
  STRENGTHS="${STRENGTHS}- Descriptive PR title\n"
  ((STRENGTH_COUNT++)) || true
fi

# Has PR body/description?
if [[ -n "$PR_BODY" && ${#PR_BODY} -gt 20 ]]; then
  STRENGTHS="${STRENGTHS}- Well-documented PR with detailed description\n"
  ((STRENGTH_COUNT++)) || true
fi

# Focused change?
if [[ $SRC_FILES -le 3 && $TOTAL_CHANGES -lt 200 ]]; then
  STRENGTHS="${STRENGTHS}- Focused, scoped changes\n"
  ((STRENGTH_COUNT++)) || true
fi

# Has tests?
if [[ $TEST_FILES -gt 0 ]]; then
  STRENGTHS="${STRENGTHS}- Includes test coverage (${TEST_FILES} test file(s))\n"
  ((STRENGTH_COUNT++)) || true
fi

# --- Calculate confidence ---
CONFIDENCE="Medium"
CONFIDENCE_EMOJI="🟡"
SCORE=50

# Base score from focus
if [[ $SRC_FILES -le 3 ]]; then
  SCORE=$((SCORE + 15))
fi
if [[ $TOTAL_CHANGES -lt 200 ]]; then
  SCORE=$((SCORE + 15))
fi
if [[ $TEST_FILES -gt 0 ]]; then
  SCORE=$((SCORE + 15))
fi
if [[ ${#PR_TITLE} -ge 10 && -n "$PR_BODY" ]]; then
  SCORE=$((SCORE + 10))
fi
# Penalize risks
SCORE=$((SCORE - (RISK_COUNT * 10)))
# Bonus for strengths
SCORE=$((SCORE + (STRENGTH_COUNT * 3)))

if [[ $SCORE -ge 70 ]]; then
  CONFIDENCE="High"
  CONFIDENCE_EMOJI="🟢"
elif [[ $SCORE -le 35 ]]; then
  CONFIDENCE="Low"
  CONFIDENCE_EMOJI="🔴"
fi

# Clamp
if [[ $SCORE -gt 95 ]]; then SCORE=95; fi
if [[ $SCORE -lt 5 ]]; then SCORE=5; fi

# --- Build file details (if verbose) ---
if [[ $VERBOSE -eq 1 ]]; then
  FILE_DETAILS="\n### 🔍 File-by-File Details\n<details>\n<summary>Click to expand</summary>\n\n"
  
  # Extract per-file stats from diff
  while IFS= read -r line; do
    if [[ "$line" =~ ^diff\ --git\ a/(.*)\ b/(.*) ]]; then
      FILE_DETAILS="${FILE_DETAILS}\n#### \`${BASH_REMATCH[2]}\`\n"
    elif [[ "$line" =~ ^@@\ -([0-9,]+)\ \+([0-9,]+)\ @@ ]]; then
      FILE_DETAILS="${FILE_DETAILS}- Lines changed: ${BASH_REMATCH[1]} → ${BASH_REMATCH[2]}\n"
    fi
  done <<< "$DIFF"
  
  FILE_DETAILS="${FILE_DETAILS}\n</details>"
fi

# --- Assemble output ---
REVIEW="## 📋 PR Review: #${PR_NUM} — ${PR_TITLE}

**${CONFIDENCE_EMOJI} Confidence:** ${CONFIDENCE} (**${SCORE}/100**) | **Files:** ${PR_CHANGED_FILES} | **Lines:** +${PR_ADDITIONS}/-${PR_DELETIONS} | **Author:** @${PR_AUTHOR}

### Summary
This PR modifies ${PR_CHANGED_FILES} file(s) with ${TOTAL_CHANGES} total lines of diff. "

# Auto-generate summary
if [[ $RISK_COUNT -eq 0 ]]; then
  REVIEW="${REVIEW}The changes look clean with no significant risks identified."
else
  REVIEW="${REVIEW}While the changes are generally sound, there are ${RISK_COUNT} item(s) that warrant attention (see Risks below)."
fi

REVIEW="${REVIEW}
"

if [[ $STRENGTH_COUNT -gt 0 ]]; then
  REVIEW="${REVIEW}### ✅ Strengths
${STRENGTHS}
"
fi

if [[ $RISK_COUNT -gt 0 ]]; then
  REVIEW="${REVIEW}### ⚠️ Risks
${RISKS}
"
fi

if [[ $SUGGESTION_COUNT -gt 0 ]]; then
  REVIEW="${REVIEW}### 💡 Suggestions
${SUGGESTIONS}
"
fi

REVIEW="${REVIEW}${FILE_DETAILS}
---
*Generated by PR Review Agent*"

# --- Output or post ---
if [[ $DRY_RUN -eq 1 ]]; then
  echo -e "$REVIEW"
else
  if [[ -n "$GITHUB_TOKEN" ]]; then
    # Post as PR comment
    BODY_ESCAPED=$(echo -e "$REVIEW" | jq -Rs .)
    $GH_CMD "repos/${OWNER}/${REPO}/issues/${PR_NUM}/comments" \
      -f body="$BODY_ESCAPED" > /dev/null 2>&1 && \
      echo "✅ Review posted to ${OWNER}/${REPO}#${PR_NUM}" || \
      echo "❌ Failed to post review"
  else
    # Use gh command to post
    echo -e "$REVIEW" | gh pr comment ${PR_NUM} --repo "${OWNER}/${REPO}" --body-file - 2>/dev/null && \
      echo "✅ Review posted to ${OWNER}/${REPO}#${PR_NUM}" || {
      echo "---"
      echo -e "$REVIEW"
      echo ""
      echo "(Run with --dry-run to output to stdout, or set GITHUB_TOKEN)"
    }
  fi
fi
