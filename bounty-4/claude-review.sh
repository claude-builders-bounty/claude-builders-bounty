#!/usr/bin/env bash
# claude-review — Review a PR and post a structured Markdown comment.
#
# Usage:
#   claude-review --pr https://github.com/owner/repo/pull/123
#   claude-review --pr https://github.com/owner/repo/pull/123 --post
#
# Requires:
#   - gh CLI authenticated
#   - ANTHROPIC_API_KEY env var set
#
# The review includes:
#   - Summary of changes (2-3 sentences)
#   - Identified risks (list)
#   - Improvement suggestions (list)
#   - Overall assessment (approve/request changes/needs discussion)

set -euo pipefail

PR_URL=""
POST_COMMENT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2;;
    --post) POST_COMMENT=true; shift;;
    -h|--help) echo "Usage: claude-review --pr <PR_URL> [--post]"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required" >&2
  exit 1
fi

# Parse PR URL: https://github.com/owner/repo/pull/123
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
else
  echo "Error: Invalid PR URL. Expected: https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

echo "Reviewing PR #$PR_NUM in $OWNER/$REPO..."

# Fetch PR metadata and diff
PR_JSON=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json title,body,additions,deletions,changedFiles,files,commits)
PR_DIFF=$(gh pr diff "$PR_NUM" --repo "$OWNER/$REPO" 2>/dev/null || echo "Diff not available")

# Extract key info
TITLE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
ADDITIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['additions'])")
DELETIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['deletions'])")
CHANGED_FILES=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['changedFiles'])")
FILE_LIST=$(echo "$PR_JSON" | python3 -c "import sys,json; [print(f'  - {f[\"path\"]}') for f in json.load(sys.stdin)['files']]")

# Build the prompt
PROMPT="You are a senior code reviewer. Analyze this pull request and provide a structured Markdown review.

## PR Title
$TITLE

## Stats
- Files changed: $CHANGED_FILES
- Additions: +$ADDITIONS
- Deletions: -$DELETIONS

## Changed Files
$FILE_LIST

## Diff
\`\`\`diff
$PR_DIFF
\`\`\`

## Output Format
Provide your review in this format:

### Summary
(2-3 sentences summarizing what this PR does)

### Identified Risks
- (List specific risks, if any)

### Improvement Suggestions
- (List specific, actionable suggestions)

### Overall Assessment
(APPROVE / REQUEST CHANGES / NEEDS DISCUSSION — with one-line justification)"

# Call Claude API
REVIEW=$(python3 -c "
import os, json, urllib.request

api_key = os.environ.get('ANTHROPIC_API_KEY', '')
prompt = '''$PROMPT'''

if api_key:
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        data=json.dumps({
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 4096,
            'messages': [{'role': 'user', 'content': prompt}]
        }).encode()
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(data['content'][0]['text'])
else:
    # Fallback: generate a basic review without Claude
    print('''### Summary
This PR modifies $CHANGED_FILES files with +$ADDITIONS/-$DELETIONS lines.

### Identified Risks
- (Set ANTHROPIC_API_KEY for AI-powered risk analysis)

### Improvement Suggestions
- (Set ANTHROPIC_API_KEY for AI-powered suggestions)

### Overall Assessment
NEEDS DISCUSSION — Set ANTHROPIC_API_KEY for full AI review.''')
")

if [[ "$POST_COMMENT" == "true" ]]; then
  gh pr comment "$PR_NUM" --repo "$OWNER/$REPO" --body "$REVIEW"
  echo "Review posted to PR #$PR_NUM"
else
  echo "$REVIEW"
  echo ""
  echo "---"
  echo "To post this review as a comment, run: claude-review --pr $PR_URL --post"
fi
