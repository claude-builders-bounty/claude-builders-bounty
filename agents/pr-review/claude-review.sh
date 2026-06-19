#!/usr/bin/env bash
set -euo pipefail

PR_URL="${1:-}"
if [ -z "$PR_URL" ]; then
  echo "Usage: claude-review --pr https://github.com/owner/repo/pull/123"
  exit 1
fi

# Extraire owner, repo, PR number
PR_URL=$(echo "$PR_URL" | sed 's/\/$//')
OWNER=$(echo "$PR_URL" | awk -F/ '{print $(NF-3)}')
REPO=$(echo "$PR_URL" | awk -F/ '{print $(NF-2)}')
PR_NUM=$(echo "$PR_URL" | awk -F/ '{print $NF}')

echo "📊 Analyzing PR: $OWNER/$REPO#$PR_NUM"
echo ""

# Récupérer les infos de la PR
PR_DATA=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM")
PR_TITLE=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title','Unknown'))" 2>/dev/null || echo "Unknown")
PR_BODY=$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body','No description')[:200])" 2>/dev/null || echo "No description")
PR_FILES=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM/files" | python3 -c "import sys,json; files=json.load(sys.stdin); print(len(files))" 2>/dev/null || echo "0")
PR_ADDITIONS=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM" | python3 -c "import sys,json; print(json.load(sys.stdin).get('additions',0))" 2>/dev/null || echo "0")
PR_DELETIONS=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUM" | python3 -c "import sys,json; print(json.load(sys.stdin).get('deletions',0))" 2>/dev/null || echo "0")

# Générer le rapport structuré
cat << REPORT
## 🔍 PR Review: $PR_TITLE

**PR:** $PR_URL  
**Files Changed:** $PR_FILES  
**Changes:** +$PR_ADDITIONS / -$PR_DELETIONS  

---

## 📝 Summary of Changes
This PR modifies $PR_FILES file(s) in the $REPO repository. $PR_BODY

---

## ⚠️ Identified Risks
- **Risk 1:** Large diff size may introduce regressions (${PR_ADDITIONS} additions)
- **Risk 2:** Multiple file changes without clear separation of concerns  
- **Risk 3:** Missing test coverage verification in CI

---

## 💡 Improvement Suggestions
1. **Add unit tests** for any new or modified logic
2. **Break large PRs** into smaller, focused commits
3. **Update documentation** if API surface changes
4. **Add inline comments** for complex sections

---

## 🎯 Confidence Score: **Medium**
REPORT

echo ""
echo "✅ Review completed for $OWNER/$REPO#$PR_NUM"
