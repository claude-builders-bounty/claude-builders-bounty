#!/usr/bin/env bash
set -euo pipefail

PR_URL="${1:-}"
if [ -z "$PR_URL" ]; then
  echo "Usage: claude-review --pr <PR_URL>"
  echo "Example: claude-review --pr https://github.com/owner/repo/pull/123"
  exit 1
fi

OWNER_REPO=$(echo "$PR_URL" | sed -n 's|.*github.com/\([^/]*/[^/]*\)/pull/.*|\1|p')
PR_NUM=$(echo "$PR_URL" | sed -n 's|.*/pull/\([0-9]*\).*|\1|p')

if [ -z "$OWNER_REPO" ] || [ -z "$PR_NUM" ]; then
  echo "Error: Could not parse PR URL. Expected format: https://github.com/owner/repo/pull/123"
  exit 1
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable not set"
  exit 1
fi

echo "Reviewing $OWNER_REPO PR #$PR_NUM..."
echo ""

echo "--- PR Metadata ---"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM" | \
  jq -r '"Title: \(.title)\nAuthor: \(.user.login)\nState: \(.state)\nCreated: \(.created_at)\nDescription: \(.body // "N/A")\n"'

DIFF=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM")

echo "--- Commits ---"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM/commits" | \
  jq -r '.[] | "* \(.sha[0:7]): \(.commit.message | split("\n")[0]) by \(.commit.author.name)"'

echo ""
echo "--- Files Changed ---"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM/files" | \
  jq -r '.[] | "* \(.filename) (\(.status), +\(.additions)/-\(.deletions))"'

echo ""
echo "--- Diff Stats ---"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM" | \
  jq -r '"Total: +\(.additions)/-\(.deletions) across \(.changed_files) files"'

echo ""
echo "═══════════════════════════════════════════════"
echo "            PR REVIEW                          "
echo "═══════════════════════════════════════════════"
echo ""

CHANGED_FILES=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM/files" | jq 'length')
PR_DATA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM")
ADDITIONS=$(echo "$PR_DATA" | jq -r '.additions')
DELETIONS=$(echo "$PR_DATA" | jq -r '.deletions')
TITLE=$(echo "$PR_DATA" | jq -r '.title')

RISKS=""
SUGGESTIONS=""

if echo "$DIFF" | grep -qiE "password|secret|token|api.key|credential|GH_TOKEN|ghp_|sk-ant"; then
  RISKS="$RISKS
- Possible credential or secret exposure in diff"
  SUGGESTIONS="$SUGGESTIONS
- Review diff for hardcoded secrets; use environment variables or GitHub secrets"
fi

if [ "$ADDITIONS" -gt 500 ]; then
  RISKS="$RISKS
- Large PR ($ADDITIONS additions) -- review risk of breaking changes"
  SUGGESTIONS="$SUGGESTIONS
- Consider splitting into smaller PRs for easier review"
fi

if echo "$DIFF" | grep -qiE "TODO|FIXME|HACK|XXX|WORKAROUND"; then
  SUGGESTIONS="$SUGGESTIONS
- Resolve TODO/FIXME/HACK/WORKAROUND comments before merge"
fi

if echo "$DIFF" | grep -qiE "console\.log|print\(|println\!|print!|dbg\!|eprintln"; then
  SUGGESTIONS="$SUGGESTIONS
- Remove debug logging statements before merge"
fi

if echo "$DIFF" | grep -qiE "DROP TABLE|TRUNCATE|rm -rf /|DROP DATABASE|DELETE FROM"; then
  RISKS="$RISKS
- Contains destructive operations (DROP/TRUNCATE/rm -rf)"
fi

if [ -z "$RISKS" ]; then
  RISKS="- No significant risks identified"
fi

if [ -z "$SUGGESTIONS" ]; then
  SUGGESTIONS="- No specific improvement suggestions"
fi

CONFIDENCE="High"
[ "$CHANGED_FILES" -gt 20 ] && CONFIDENCE="Medium"
[ "$CHANGED_FILES" -gt 50 ] && CONFIDENCE="Low"

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  DIFF_TRUNC=$(echo "$DIFF" | head -c 50000)
  read -r -d '' PROMPT << 'EOPROMPT' || true
You are a code review assistant. Analyze the following PR diff and produce a structured markdown review.

### Summary
2-3 sentences describing what this PR does.

### Identified Risks
- List each risk as a bullet point
- Note security concerns, breaking changes, or edge cases

### Improvement Suggestions
- List concrete, actionable improvements
- Include code snippets where helpful

### Confidence Score
**Confidence: [Low/Medium/High]**

Base your confidence on:
- Low: Large diff, complex logic, unclear intent, or unsafe operations
- Medium: Reasonable changes with minor concerns
- High: Simple, clear, well-structured changes

Now analyze this diff:
EOPROMPT

  RESULT=$(curl -s https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "$(jq -n --arg diff "$DIFF_TRUNC" --arg prompt "$PROMPT" '{
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      messages: [
        {role: "user", content: $prompt + "\n\n```diff\n" + $diff + "\n```"}
      ]
    }')")

  echo "$RESULT" | jq -r '.content[0].text // "Error: Could not generate review"'
else
  echo "--- Analysis (Rule-based) ---"
  echo ""
  cat <<EOF
## PR Review: $TITLE

**Repository:** $OWNER_REPO
**PR Number:** #$PR_NUM

### Summary
This PR changes **$CHANGED_FILES files** (+$ADDITIONS / -$DELETIONS lines).

### Identified Risks
$RISKS

### Improvement Suggestions
$SUGGESTIONS

### Confidence Score
**$CONFIDENCE**
EOF
fi
