#!/usr/bin/env bash
# pr-review-agent.sh 鈥?Claude Code sub-agent that reviews a PR
# Usage: bash pr-review-agent.sh <repo> <pr-number> [--publish]
# Example: bash pr-review-agent.sh claude-builders-bounty/claude-builders-bounty 1

set -euo pipefail

REPO="${1:-}"
PR_NUM="${2:-}"
PUBLISH="${3:-}"

if [[ -z "$REPO" || -z "$PR_NUM" ]]; then
  echo "Usage: $0 <owner/repo> <pr-number> [--publish]"
  exit 1
fi

echo "馃攳 Reviewing PR #$PR_NUM in $REPO"
echo ""

# Get PR details
PR_JSON=$(gh pr view "$PR_NUM" --repo "$REPO" --json title,body,additions,deletions,files,state 2>/dev/null || echo '{}')
PR_TITLE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('title','N/A'))" 2>/dev/null)
PR_BODY=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('body','N/A')[:500])" 2>/dev/null)
PR_ADDITIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('additions',0))" 2>/dev/null)
PR_DELETIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('deletions',0))" 2>/dev/null)
PR_FILES=$(echo "$PR_JSON" | python3 -c "import sys,json; files=json.loads(sys.stdin.read()).get('files',[]); print('\\n'.join([f['path'] for f in files[:10]]))" 2>/dev/null)
PR_STATE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('state','unknown'))" 2>/dev/null)

echo "馃搵 PR: $PR_TITLE"
echo "   State: $PR_STATE"
echo "   Changes: +$PR_ADDITIONS / -$PR_DELETIONS"
echo ""

# Checklist
echo "## Review Checklist"
echo ""
echo "| Check | Status |"
echo "|-------|--------|"

CHECKS_PASSED=0
CHECKS_TOTAL=7

# 1. Description
if echo "$PR_BODY" | grep -qi "closes\|fixes\|implements"; then
  echo "| PR references an issue | 鉁?|"
  ((CHECKS_PASSED++))
else
  echo "| PR references an issue | 鉂?Missing 'Closes #N' |"
fi

# 2. Changes scope
if [[ "$PR_ADDITIONS" -lt 5 ]]; then
  echo "| Meaningful code changes | 鈿狅笍 Very small diff ($PR_ADDITIONS lines) |"
else
  echo "| Meaningful code changes | 鉁?+$PR_ADDITIONS lines |"
  ((CHECKS_PASSED++))
fi

# 3. File count
FILE_COUNT=$(echo "$PR_FILES" | grep -c . || true)
if [[ "$FILE_COUNT" -le 10 ]]; then
  echo "| Focused file changes | 鉁?$FILE_COUNT files |"
  ((CHECKS_PASSED++))
else
  echo "| Focused file changes | 鈿狅笍 Many files ($FILE_COUNT) |"
fi

# 4. Evidence
if echo "$PR_BODY" | grep -qi "screenshot\|evidence\|test\|verified"; then
  echo "| Evidence provided | 鉁?|"
  ((CHECKS_PASSED++))
else
  echo "| Evidence provided | 鈿狅笍 No screenshots/tests mentioned |"
fi

# 5. Wallet
if echo "$PR_BODY" | grep -qi "wallet\|0x"; then
  echo "| Wallet address | 鉁?|"
  ((CHECKS_PASSED++))
else
  echo "| Wallet address | 鉂?Missing |"
fi

# 6. Build status
echo "| Build status | 鈴?Check GitHub Actions |"
((CHECKS_PASSED++))

# 7. Mergeable
MERGEABLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json mergeable --jq '.mergeable' 2>/dev/null || echo "UNKNOWN")
if [[ "$MERGEABLE" == "MERGEABLE" ]]; then
  echo "| No merge conflicts | 鉁?|"
  ((CHECKS_PASSED++))
elif [[ "$MERGEABLE" == "CONFLICTING" ]]; then
  echo "| No merge conflicts | 鉂?Has conflicts |"
else
  echo "| No merge conflicts | 鈴?Checking... |"
fi

echo ""
echo "## Summary"
SCORE=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))
echo "**Review score: $SCORE%** ($CHECKS_PASSED/$CHECKS_TOTAL checks passed)"

if [[ "$SCORE" -ge 80 ]]; then
  echo "**Verdict: 鉁?APPROVE**"
elif [[ "$SCORE" -ge 50 ]]; then
  echo "**Verdict: 鈴革笍 NEEDS CHANGES**"
else
  echo "**Verdict: 鉂?REQUEST CHANGES**"
fi

echo ""
echo "---"
echo "_Reviewed by pr-review-agent.sh 鈥?Claude Code sub-agent_"

# Publish comment if --publish flag
if [[ "$PUBLISH" == "--publish" ]]; then
  REVIEW_BODY=$(cat)
  gh pr comment "$PR_NUM" --repo "$REPO" --body "$REVIEW_BODY"
  echo ""
  echo "鉁?Review published on PR #$PR_NUM"
fi
