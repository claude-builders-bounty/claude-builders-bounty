#!/bin/bash
# claude-review.sh — PR review sub-agent
# Usage: bash claude-review.sh --pr <PR_URL>
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

PR_URL=""; DIFF_FILE=""; OUTPUT_FILE=""
while [[ $# -gt 0 ]]; do
  case $1 in --pr) PR_URL="$2"; shift 2 ;; --diff) DIFF_FILE="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help) echo "Usage: bash claude-review.sh --pr <PR_URL> [--output <file>]"; exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;; esac
done

# Fetch diff
DIFF=""
if [ -n "$PR_URL" ]; then
  echo -e "${BLUE}Fetching PR diff...${NC}"
  PR_PATH=$(echo "$PR_URL" | sed -E 's|https?://github.com/||' | sed 's|/pull/.*||')
  PR_NUM=$(echo "$PR_URL" | sed 's|.*/pull/||;s|/.*||;s|[^0-9]||g')
  [ -z "$PR_NUM" ] && PR_NUM="?"
  
  DIFF=$(curl -sL -H "Authorization: token ${GITHUB_TOKEN:-}" \
    -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/${PR_PATH}/pulls/${PR_NUM}" 2>/dev/null || true)
    
  if [ -z "$DIFF" ]; then
    DIFF=$(curl -sL "https://github.com/${PR_PATH}/pull/${PR_NUM}.diff" 2>/dev/null || true)
  fi
  [ -z "$DIFF" ] && { echo -e "${RED}Failed to fetch diff${NC}"; exit 1; }
elif [ -n "$DIFF_FILE" ]; then
  DIFF=$(cat "$DIFF_FILE")
else
  echo -e "${RED}Specify --pr or --diff${NC}"
  exit 1
fi

# Analyze
echo -e "${BLUE}Analyzing...${NC}"

FILES_CHANGED=$(echo "$DIFF" | grep -c '^diff --git' || echo 0)
ADDITIONS=$(echo "$DIFF" | grep -c '^+' || echo 0)
DELETIONS=$(echo "$DIFF" | grep -c '^-' || echo 0)
TOTAL=$((ADDITIONS + DELETIONS))
[ -z "$TOTAL" ] && TOTAL=0

FILES=()
while IFS= read -r line; do
  FILES+=("$(echo "$line" | sed 's|diff --git a/||;s| b/.*||')")
done < <(echo "$DIFF" | grep '^diff --git')

RISKS=(); SUGGESTIONS=()

# Large PR
[ "$TOTAL" -gt 500 ] 2>/dev/null && RISKS+=("Large PR (${TOTAL} lines)") && SUGGESTIONS+=("Split into smaller PRs (<500 lines)")

# TODOs
TODOS=$(echo "$DIFF" | grep '^+' | grep -ci 'TODO\|FIXME\|HACK\|XXX' || echo 0)
[ "${TODOS:-0}" -gt 0 ] 2>/dev/null && RISKS+=("${TODOS} TODO/FIXME markers") && SUGGESTIONS+=("Address TODOs before merge")

# Secrets
SECRETS=$(echo "$DIFF" | grep '^+' | grep -ciE '(api.?key|secret|password|token|credential)[:=].*["'"'"'"]?(sk-|ghp_|AKIA)' || echo 0)
[ "${SECRETS:-0}" -gt 0 ] 2>/dev/null && RISKS+=("${SECRETS} potential hardcoded secrets") && SUGGESTIONS+=("Use env vars for secrets")

# Debug
DEBUG=$(echo "$DIFF" | grep '^+' | grep -ci 'console\.log\|fmt\.Print\|debugger' || echo 0)
[ "${DEBUG:-0}" -gt 0 ] 2>/dev/null && RISKS+=("${DEBUG} debug statements") && SUGGESTIONS+=("Remove debug statements")

# Large files
for f in "${FILES[@]}"; do
  adds=$(echo "$DIFF" | awk -v f="$f" '/^diff --git/{if($0~f){found=1;next}} found && /^\+/{count++} found && /^diff --git/{if(!($0~f)){found=0}} END{print count+0}')
  [ "${adds:-0}" -gt 200 ] 2>/dev/null && RISKS+=("Large file: ${f} (+${adds} lines)") && SUGGESTIONS+=("Refactor ${f} into smaller modules")
done

# Missing tests
HAS_TESTS=$(echo "$DIFF" | grep -c '^diff --git.*test\|^diff --git.*spec\|^diff --git.*__tests__' || echo 0)
HAS_CODE=$(echo "$DIFF" | grep -c '^diff --git.*\.\(go\|py\|js\|ts\|jsx\|tsx\|java\|rb\)' || echo 0)
[ "${HAS_CODE:-0}" -gt 0 ] && [ "${HAS_TESTS:-0}" -eq 0 ] 2>/dev/null && SUGGESTIONS+=("Add tests for code changes")

# Dependency changes
DEPS=$(echo "$DIFF" | grep -c '^diff --git.*\(go\.mod\|go\.sum\|package\.json\|requirements\.txt\)' || echo 0)
[ "${DEPS:-0}" -gt 0 ] 2>/dev/null && SUGGESTIONS+=("Verify dependency changes")

# Confidence
RISK_COUNT=${#RISKS[@]}
if [ "$RISK_COUNT" -eq 0 ] && [ "${TOTAL:-0}" -lt 100 ] 2>/dev/null; then
  CONFIDENCE="High"; CONF_COLOR="${GREEN}"
elif [ "$RISK_COUNT" -le 2 ] && [ "${TOTAL:-0}" -lt 300 ] 2>/dev/null; then
  CONFIDENCE="Medium"; CONF_COLOR="${YELLOW}"
else
  CONFIDENCE="Low"; CONF_COLOR="${RED}"
fi

# Output
OUTPUT="## 🔍 PR Review: ${PR_PATH:+${PR_PATH} #}${PR_NUM:-?}

### 📊 Summary
- **Files changed:** ${FILES_CHANGED:-0}
- **Additions:** ${ADDITIONS:-0} | **Deletions:** ${DELETIONS:-0}
- **Total changes:** ${TOTAL:-0} lines

### 📁 Files Modified
| File | Status |
|------|--------|"
for f in "${FILES[@]}"; do OUTPUT+="\n| \`${f}\` | Modified |"; done

if [ ${#RISKS[@]} -gt 0 ]; then
  OUTPUT+="\n\n### ⚠️ Identified Risks"
  for r in "${RISKS[@]}"; do OUTPUT+="\n- 🔴 ${r}"; done
fi

if [ ${#SUGGESTIONS[@]} -gt 0 ]; then
  OUTPUT+="\n\n### 💡 Improvement Suggestions"
  for s in "${SUGGESTIONS[@]}"; do OUTPUT+="\n- ✅ ${s}"; done
fi

OUTPUT+="\n\n### 🎯 Confidence Score\n**${CONFIDENCE}**\n\n${RISK_COUNT} risk(s) across ${TOTAL:-0} lines in ${FILES_CHANGED:-0} file(s)
\n---\n_Reviewed by claude-review | https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4_"

if [ -n "$OUTPUT_FILE" ]; then echo -e "$OUTPUT" > "$OUTPUT_FILE"; echo -e "${GREEN}Saved to ${OUTPUT_FILE}${NC}"; fi
echo -e "\n${OUTPUT}\n${GREEN}Done.${NC}"
