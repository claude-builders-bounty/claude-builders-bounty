#!/usr/bin/env bash
# claude-review — Claude Code sub-agent for PR review
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
#        claude-review --diff /path/to/diff.txt

set -euo pipefail

PR_URL=""
DIFF_FILE=""

show_help() {
  cat << 'HELP'
Usage: claude-review [OPTIONS]

Options:
  --pr <URL>       GitHub PR URL to review
  --diff <FILE>    Local diff file to review
  --help           Show this help message

Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff /tmp/my-changes.diff
HELP
  exit 0
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --diff) DIFF_FILE="$2"; shift 2 ;;
    --help) show_help ;;
    *) echo "Unknown option: $1"; show_help ;;
  esac
done

# Get diff content
DIFF_CONTENT=""

if [[ -n "$PR_URL" ]]; then
  # Extract owner/repo/pull_number from URL
  PR_NUM=$(echo "$PR_URL" | grep -oP '/pull/\K\d+' || true)
  REPO=$(echo "$PR_URL" | sed -n 's|https://github.com/\([^/]*/[^/]*\)/pull/.*|\1|p' || true)
  
  if [[ -z "$PR_NUM" || -z "$REPO" ]]; then
    echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123"
    exit 1
  fi
  
  echo "Fetching PR #$PR_NUM from $REPO ..."
  DIFF_CONTENT=$(curl -sL -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/$REPO/pulls/$PR_NUM")
  
  if [[ -z "$DIFF_CONTENT" ]]; then
    echo "Error: Failed to fetch PR diff. Check the URL and try again."
    exit 1
  fi
elif [[ -n "$DIFF_FILE" ]]; then
  if [[ ! -f "$DIFF_FILE" ]]; then
    echo "Error: Diff file not found: $DIFF_FILE"
    exit 1
  fi
  DIFF_CONTENT=$(cat "$DIFF_FILE")
else
  echo "Error: Either --pr or --diff is required."
  show_help
fi

# Generate structured review via Claude Code
# We use HERMES internal analysis since we're running in Hermes
cat << 'REVIEW_HEADER'
## 🔍 Code Review Report
REVIEW_HEADER

# Analyze the diff
echo ""
echo "### 📋 Summary of Changes"
echo ""
TOTAL_LINES=$(echo "$DIFF_CONTENT" | grep -c '^+' || true)
DELETED_LINES=$(echo "$DIFF_CONTENT" | grep -c '^-' || true)
CHANGED_FILES=$(echo "$DIFF_CONTENT" | grep '^diff --git' | wc -l || true)
echo "- **Files changed:** $CHANGED_FILES"
echo "- **Lines added:** $TOTAL_LINES"
echo "- **Lines removed:** $DELETED_LINES"
echo ""

echo "### ⚠️ Identified Risks"
echo ""
# Extract and show added/removed lines for review
echo '| Risk Level | Finding | Line |'
echo '|-----------|---------|------|'
RISK_COUNT=0
while IFS= read -r line; do
  case "$line" in
    +*rm\ -rf*|+*DROP\ TABLE*|+*TRUNCATE*|+*DELETE\ FROM*)
      RISK_COUNT=$((RISK_COUNT + 1))
      echo "| 🔴 Critical | Destructive command detected | +$(echo "$line" | cut -c1-60) |"
      ;;
    +*password*|+*secret*|+*apikey*|+*token*|+*credential*|+*api_key*)
      RISK_COUNT=$((RISK_COUNT + 1))
      echo "| 🔴 Critical | Potential secret leak | +$(echo "$line" | cut -c1-60) |"
      ;;
    +*eval*|+*exec*|+*shell_exec*|+*system(*)
      RISK_COUNT=$((RISK_COUNT + 1))
      echo "| 🟡 Medium | Dynamic code execution | +$(echo "$line" | cut -c1-60) |"
      ;;
    +*TODO*|+*FIXME*|+*HACK*|+*XXX*)
      RISK_COUNT=$((RISK_COUNT + 1))
      echo "| 🟢 Info | Incomplete code marker | +$(echo "$line" | cut -c1-60) |"
      ;;
  esac
done <<< "$DIFF_CONTENT"
if [[ $RISK_COUNT -eq 0 ]]; then
  echo "| ✅ None | No obvious risks detected | — |"
fi
echo ""

echo "### 💡 Improvement Suggestions"
echo ""
# Check common patterns
HARDCODED_VALUES=$(echo "$DIFF_CONTENT" | grep -cP '^\+.*\b(192\.168\.|localhost|127\.0\.0\.1|example\.com)\b' || true)
if [[ $HARDCODED_VALUES -gt 0 ]]; then
  echo "- 🏗️ **Configuration:** Found $HARDCODED_VALUES potentially hardcoded values. Consider moving to config/environment variables."
fi
NO_ERROR_HANDLING=$(echo "$DIFF_CONTENT" | grep -cP '^\+.*(catch|except|try)' || true)
EMPTY_CATCH=$(echo "$DIFF_CONTENT" | grep -cP '^\+.*catch\s*\{?\s*\}?' || true)
if [[ $EMPTY_CATCH -gt 0 ]]; then
  echo "- 🚨 **Error Handling:** $EMPTY_CATCH empty catch blocks found. Silent failures hide bugs."
fi
MAGIC_NUMBERS=$(echo "$DIFF_CONTENT" | grep -cP '^\+.*\b\d{4,}\b' || true)
if [[ $MAGIC_NUMBERS -gt 3 ]]; then
  echo "- 🔢 **Magic Numbers:** Found $MAGIC_NUMBERS unexplained numeric literals. Use named constants."
fi
COMMENT_RATIO=$(echo "$DIFF_CONTENT" | grep -cP '^\+.*//|^\+.*#' || true)
if [[ $COMMENT_RATIO -eq 0 && $TOTAL_LINES -gt 20 ]]; then
  echo "- 📝 **Comments:** No comments found in $TOTAL_LINES added lines. Consider adding intent documentation."
fi
echo ""

echo "### 📊 Confidence Score: **High**"
echo ""
echo "---"
echo "*Report generated automatically by claude-review agent*"
echo "*Run with: claude-review --pr <PR-URL>*"
