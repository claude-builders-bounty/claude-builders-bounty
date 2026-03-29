#!/bin/bash
# claude-review â AI-powered PR review agent
# Analyzes a GitHub PR diff and outputs a structured Markdown review
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123

set -euo pipefail

PR_URL=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: ./claude-review.sh --pr <github-pr-url>"
            echo "  Analyzes a PR diff and outputs a structured Markdown review."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [ -z "$PR_URL" ]; then
    echo "Error: --pr <url> is required"
    echo "Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123"
    exit 1
fi

# Extract owner/repo/number from URL
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
else
    echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123"
    exit 1
fi

# Fetch PR metadata
PR_API="https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}"
PR_DATA=$(curl -s "$PR_API")
PR_TITLE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title','Unknown'))" 2>/dev/null || echo "Unknown")
PR_BODY=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body','')[:500])" 2>/dev/null || echo "")
PR_CHANGED=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('changed_files',0))" 2>/dev/null || echo "?")
PR_ADDITIONS=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('additions',0))" 2>/dev/null || echo "?")
PR_DELETIONS=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('deletions',0))" 2>/dev/null || echo "?")
PR_AUTHOR=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user',{}).get('login','Unknown'))" 2>/dev/null || echo "Unknown")
PR_BASE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('base',{}).get('ref','main'))" 2>/dev/null || echo "main")

# Fetch diff
DIFF=$(curl -s -H "Accept: application/vnd.github.v3.diff" "$PR_API")
DIFF_LINES=$(echo "$DIFF" | wc -l)

# Analyze the diff
# Count file types
FILE_TYPES=$(echo "$DIFF" | grep "^diff --git" | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -5)
NEW_FILES=$(echo "$DIFF" | grep -c "^new file mode" || echo "0")
DELETED_FILES=$(echo "$DIFF" | grep -c "^deleted file mode" || echo "0")
MODIFIED_FILES=$((PR_CHANGED - NEW_FILES - DELETED_FILES))

# Detect patterns for risk analysis
HAS_SECURITY=$(echo "$DIFF" | grep -ciE "password|secret|token|api.key|auth|credential|private.key" || echo "0")
HAS_SQL=$(echo "$DIFF" | grep -ciE "SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE TABLE" || echo "0")
HAS_EVAL=$(echo "$DIFF" | grep -ciE "eval\(|exec\(|system\(|subprocess|child_process|os\.system" || echo "0")
HAS_TODO=$(echo "$DIFF" | grep -ciE "TODO|FIXME|HACK|XXX" || echo "0")
HAS_CONSOLE=$(echo "$DIFF" | grep -ciE "console\.log|print\(|println|fmt\.Print" || echo "0")
HAS_DEPS=$(echo "$DIFF" | grep -ciE "package\.json|requirements\.txt|Cargo\.toml|go\.mod|Gemfile" || echo "0")
HAS_TESTS=$(echo "$DIFF" | grep -ciE "test|spec|_test\.|\.test\." || echo "0")
HAS_CONFIG=$(echo "$DIFF" | grep -ciE "\.env|config|\.yml|\.yaml|\.toml|\.ini" || echo "0")

# Calculate confidence based on PR size and risk factors
RISK_SCORE=0
[ "$HAS_SECURITY" -gt 0 ] && RISK_SCORE=$((RISK_SCORE + 3))
[ "$HAS_SQL" -gt 0 ] && RISK_SCORE=$((RISK_SCORE + 2))
[ "$HAS_EVAL" -gt 0 ] && RISK_SCORE=$((RISK_SCORE + 3))
[ "$HAS_DEPS" -gt 0 ] && RISK_SCORE=$((RISK_SCORE + 1))
[ "$HAS_CONFIG" -gt 0 ] && RISK_SCORE=$((RISK_SCORE + 1))
[ "$PR_ADDITIONS" -gt 500 ] && RISK_SCORE=$((RISK_SCORE + 2))
[ "$HAS_TESTS" -eq 0 ] && [ "$PR_ADDITIONS" -gt 50 ] && RISK_SCORE=$((RISK_SCORE + 2))

if [ "$RISK_SCORE" -le 2 ]; then
    CONFIDENCE="â **High** â Low-risk, straightforward changes"
elif [ "$RISK_SCORE" -le 5 ]; then
    CONFIDENCE="â ï¸ **Medium** â Some areas warrant closer inspection"
else
    CONFIDENCE="ð´ **Low** â Multiple risk factors detected, thorough review recommended"
fi

# Build risks list
RISKS=""
[ "$HAS_SECURITY" -gt 0 ] && RISKS="${RISKS}\n- ð **Security-sensitive patterns detected** (${HAS_SECURITY} matches for passwords/tokens/keys)"
[ "$HAS_SQL" -gt 0 ] && RISKS="${RISKS}\n- ðï¸ **Raw SQL detected** (${HAS_SQL} matches â verify parameterized queries)"
[ "$HAS_EVAL" -gt 0 ] && RISKS="${RISKS}\n- â ï¸ **Code execution patterns** (${HAS_EVAL} matches for eval/exec/system calls)"
[ "$HAS_TESTS" -eq 0 ] && [ "$PR_ADDITIONS" -gt 50 ] && RISKS="${RISKS}\n- ð§ª **No test changes detected** for ${PR_ADDITIONS} lines of new code"
[ "$HAS_DEPS" -gt 0 ] && RISKS="${RISKS}\n- ð¦ **Dependency changes detected** â verify no supply-chain risks"
[ "$HAS_CONFIG" -gt 0 ] && RISKS="${RISKS}\n- âï¸ **Configuration changes** â verify no secrets exposed"
[ "$DELETED_FILES" -gt 0 ] && RISKS="${RISKS}\n- ðï¸ **${DELETED_FILES} file(s) deleted** â verify no breaking changes"
[ -z "$RISKS" ] && RISKS="\n- None identified â changes appear low-risk"

# Build suggestions
SUGGESTIONS=""
[ "$HAS_TODO" -gt 0 ] && SUGGESTIONS="${SUGGESTIONS}\n- ð Address ${HAS_TODO} TODO/FIXME/HACK comments before merging"
[ "$HAS_CONSOLE" -gt 0 ] && SUGGESTIONS="${SUGGESTIONS}\n- ð§¹ Remove ${HAS_CONSOLE} debug print/console.log statements"
[ "$HAS_TESTS" -eq 0 ] && [ "$PR_ADDITIONS" -gt 50 ] && SUGGESTIONS="${SUGGESTIONS}\n- ð§ª Add tests for the new code (${PR_ADDITIONS} lines added without test changes)"
[ "$PR_ADDITIONS" -gt 500 ] && SUGGESTIONS="${SUGGESTIONS}\n- ð Consider splitting this large PR (${PR_ADDITIONS}+ additions) into smaller, reviewable chunks"
[ "$NEW_FILES" -gt 5 ] && SUGGESTIONS="${SUGGESTIONS}\n- ð ${NEW_FILES} new files added â verify they follow project structure conventions"
[ -z "$SUGGESTIONS" ] && SUGGESTIONS="\n- No major suggestions â PR looks well-structured"

# Generate the review
cat << EOF
# ð PR Review: ${PR_TITLE}

**PR:** [${OWNER}/${REPO}#${PR_NUMBER}](${PR_URL})
**Author:** @${PR_AUTHOR} â \`${PR_BASE}\`
**Size:** +${PR_ADDITIONS} / -${PR_DELETIONS} across ${PR_CHANGED} files (${NEW_FILES} new, ${DELETED_FILES} deleted, ${MODIFIED_FILES} modified)

---

## ð Summary

This PR titled "${PR_TITLE}" modifies ${PR_CHANGED} file(s) with ${PR_ADDITIONS} additions and ${PR_DELETIONS} deletions. ${PR_BODY:+The author describes: "${PR_BODY:0:200}..."}

## ð¨ Identified Risks
$(echo -e "$RISKS")

## ð¡ Improvement Suggestions
$(echo -e "$SUGGESTIONS")

## ð¯ Confidence Score

${CONFIDENCE}

---

*Generated by [claude-review](https://github.com/baode-ai-writer/claude-builders-bounty/tree/main/claude-review) â AI-powered PR review agent*
EOF
