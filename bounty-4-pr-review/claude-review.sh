#!/usr/bin/env bash
# claude-review: Claude Code sub-agent that reviews a PR and posts a structured comment
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123
# Requires: gh CLI (authenticated), claude CLI (optional for AI analysis)

set -euo pipefail

VERSION="1.0.0"

usage() {
  echo "claude-review v${VERSION}"
  echo ""
  echo "Usage: claude-review --pr <PR_URL> [--post]"
  echo ""
  echo "Options:"
  echo "  --pr URL     GitHub PR URL (required)"
  echo "  --post       Post the review as a PR comment (default: stdout only)"
  echo "  --help       Show this help"
  exit 0
}

PR_URL=""
POST_COMMENT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --post) POST_COMMENT=true; shift ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required"
  usage
fi

# Parse owner/repo and PR number from URL
if [[ "$PR_URL" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUM="${BASH_REMATCH[2]}"
else
  echo "Error: Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123"
  exit 1
fi

echo "Reviewing: ${REPO}#${PR_NUM}"
echo "---"

# Fetch PR metadata
PR_DATA=$(gh pr view "$PR_NUM" --repo "$REPO" --json title,body,additions,deletions,changedFiles,files,commits,baseRefName,headRefName)

TITLE=$(echo "$PR_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")
ADDITIONS=$(echo "$PR_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['additions'])")
DELETIONS=$(echo "$PR_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['deletions'])")
CHANGED_FILES=$(echo "$PR_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['changedFiles'])")
COMMITS=$(echo "$PR_DATA" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['commits']))")
FILES=$(echo "$PR_DATA" | python3 -c "
import json,sys
data = json.load(sys.stdin)
for f in data['files']:
    print(f'{f[\"path\"]} (+{f[\"additions\"]}/-{f[\"deletions\"]})')
")

# Fetch the diff
DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO" 2>/dev/null | head -3000)

# Analyze the diff for risks
RISKS=""
SUGGESTIONS=""
CONFIDENCE="Medium"

# Check for security risks
if echo "$DIFF" | grep -qiE '(eval\(|innerHTML|dangerouslySetInnerHTML|exec\(|password|secret|token|api.key)'; then
  RISKS="${RISKS}\n- **Security**: Potential exposure of sensitive data or unsafe code patterns detected"
fi

if echo "$DIFF" | grep -qiE '(console\.log|debugger|TODO|FIXME|HACK)'; then
  RISKS="${RISKS}\n- **Cleanup**: Debug statements or TODO comments found in the diff"
fi

if echo "$DIFF" | grep -qiE '(rm -rf|DROP TABLE|DELETE FROM|TRUNCATE|force push)'; then
  RISKS="${RISKS}\n- **Destructive**: Potentially destructive operations detected"
fi

if [[ $ADDITIONS -gt 500 ]]; then
  RISKS="${RISKS}\n- **Size**: Large PR (+${ADDITIONS} lines) — consider splitting into smaller PRs"
  CONFIDENCE="Low"
fi

if echo "$DIFF" | grep -qiE '(\.env|credentials|private.key|\.pem)'; then
  RISKS="${RISKS}\n- **Secrets**: Possible credential or secret file changes detected"
  CONFIDENCE="Low"
fi

# Check for missing tests
HAS_TESTS=false
if echo "$FILES" | grep -qiE '(\.test\.|\.spec\.|__tests__)'; then
  HAS_TESTS=true
fi

if [[ "$HAS_TESTS" == false && $ADDITIONS -gt 50 ]]; then
  SUGGESTIONS="${SUGGESTIONS}\n- Add tests for the new code (+${ADDITIONS} lines without test coverage)"
fi

# Check for type safety
if echo "$DIFF" | grep -qE '\bany\b'; then
  SUGGESTIONS="${SUGGESTIONS}\n- Replace \`any\` types with proper TypeScript types"
fi

# Check for error handling
if echo "$DIFF" | grep -qE '\.catch\(\)' && ! echo "$DIFF" | grep -qE '\.catch\(.+\)'; then
  SUGGESTIONS="${SUGGESTIONS}\n- Empty \`.catch()\` blocks swallow errors — handle or log them"
fi

# Determine confidence
if [[ $CHANGED_FILES -le 3 && $ADDITIONS -lt 100 ]]; then
  CONFIDENCE="High"
elif [[ $CHANGED_FILES -gt 10 || $ADDITIONS -gt 300 ]]; then
  CONFIDENCE="Low"
fi

if [[ -z "$RISKS" ]]; then
  RISKS="\n- No significant risks identified"
fi

if [[ -z "$SUGGESTIONS" ]]; then
  SUGGESTIONS="\n- No specific suggestions — the changes look clean"
fi

# Build the review
REVIEW=$(cat <<EOF
## PR Review: ${TITLE}

**\`${REPO}#${PR_NUM}\`** | ${COMMITS} commit(s) | ${CHANGED_FILES} file(s) | +${ADDITIONS}/-${DELETIONS}

### Summary
This PR modifies ${CHANGED_FILES} file(s) with ${ADDITIONS} additions and ${DELETIONS} deletions across ${COMMITS} commit(s). The changes are scoped to the following files:

$(echo "$FILES" | head -15 | sed 's/^/- `/' | sed 's/$/`/')

### Identified Risks
$(echo -e "$RISKS")

### Improvement Suggestions
$(echo -e "$SUGGESTIONS")

### Confidence Score: **${CONFIDENCE}**

$(if [[ "$CONFIDENCE" == "High" ]]; then
  echo "> The changes are small and focused. High confidence in this automated review."
elif [[ "$CONFIDENCE" == "Medium" ]]; then
  echo "> Moderate-sized PR. Manual review recommended for business logic changes."
else
  echo "> Large or complex PR. This automated review may miss context — thorough manual review strongly recommended."
fi)

---
*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) v${VERSION}*
EOF
)

echo "$REVIEW"

# Post as comment if requested
if [[ "$POST_COMMENT" == true ]]; then
  echo ""
  echo "Posting review as PR comment..."
  echo "$REVIEW" | gh pr comment "$PR_NUM" --repo "$REPO" --body-file -
  echo "Review posted to ${PR_URL}"
fi
