#!/usr/bin/env bash
set -euo pipefail

usage() {
	echo "Usage: claude-review --pr <url>"
	echo "  url: https://github.com/owner/repo/pull/123"
	exit 1
}

PR_URL=""
while [[ $# -gt 0 ]]; do
	case "$1" in
		--pr) PR_URL="$2"; shift 2 ;;
		*) usage ;;
	esac
done

[ -z "$PR_URL" ] && usage

if [[ ! "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
	echo "Error: invalid PR URL" >&2
	exit 1
fi

OWNER="${BASH_REMATCH[1]}"
REPO="${BASH_REMATCH[2]}"
PR_NUM="${BASH_REMATCH[3]}"

META=$(gh pr view "$PR_URL" --json title,body,additions,deletions,changedFiles \
	--jq '"Title: \(.title)\nFiles changed: \(.changedFiles)\nAdditions: \(.additions)\nDeletions: \(.deletions)\n\nDescription:\n\(.body)"')

DIFF=$(gh pr diff "$PR_URL" --patch)

DIFF_TRUNCATED="$DIFF"
if [ ${#DIFF} -gt 50000 ]; then
	DIFF_TRUNCATED="${DIFF:0:50000}

... (diff truncated at 50000 chars)"
fi

PROMPT="Review this pull request. Be direct and specific.

PR: ${OWNER}/${REPO}#${PR_NUM}
${META}

Diff:
${DIFF_TRUNCATED}

Respond in this exact format:

## Summary
2-3 sentence summary of what this PR does.

## Risks
- List each identified risk or potential issue
- Be specific about file and line if possible

## Suggestions
- List actionable improvement suggestions
- Focus on correctness, security, and maintainability

## Confidence
**Score: [Low/Medium/High]**
Brief justification for the score."

if command -v claude &>/dev/null; then
	echo "$PROMPT" | claude -p --output-format text
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
	ESCAPED=$(jq -Rs . <<< "$PROMPT")
	RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
		-H "content-type: application/json" \
		-H "x-api-key: $ANTHROPIC_API_KEY" \
		-H "anthropic-version: 2023-06-01" \
		-d "{\"model\":\"claude-sonnet-4-20250514\",\"max_tokens\":4096,\"messages\":[{\"role\":\"user\",\"content\":${ESCAPED}}]}")
	echo "$RESPONSE" | jq -r '.content[0].text'
else
	echo "Error: requires 'claude' CLI or ANTHROPIC_API_KEY env var" >&2
	exit 1
fi
