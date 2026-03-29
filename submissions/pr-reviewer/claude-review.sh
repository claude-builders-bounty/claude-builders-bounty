#!/usr/bin/env bash
# claude-review.sh — AI-powered PR review using Claude API
# Bounty #4: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
#
# Usage:
#   bash claude-review.sh --pr https://github.com/owner/repo/pull/123
#   bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
#   bash claude-review.sh --pr https://github.com/owner/repo/pull/123 --model claude-haiku-4-5-20251001
#
# Requirements:
#   - ANTHROPIC_API_KEY env var
#   - GITHUB_TOKEN env var (optional, for private repos + higher rate limits)
#   - curl, jq, python3 (standard on most systems)

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
PR_URL=""
OUTPUT_FILE=""
MODEL="claude-haiku-4-5-20251001"
MAX_DIFF_CHARS=80000  # ~20k tokens, well within context window

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr|-p)       PR_URL="$2"; shift 2 ;;
    --output|-o)   OUTPUT_FILE="$2"; shift 2 ;;
    --model|-m)    MODEL="$2"; shift 2 ;;
    --max-diff)    MAX_DIFF_CHARS="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: bash claude-review.sh --pr <github-pr-url> [--output FILE] [--model MODEL]"
      echo ""
      echo "Required env vars:"
      echo "  ANTHROPIC_API_KEY — your Anthropic API key"
      echo ""
      echo "Optional env vars:"
      echo "  GITHUB_TOKEN — for private repos and higher GitHub rate limits"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr is required." >&2
  echo "Usage: bash claude-review.sh --pr https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "Error: ANTHROPIC_API_KEY environment variable is not set." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Extract PR info from URL
# ---------------------------------------------------------------------------
# Expected format: https://github.com/OWNER/REPO/pull/NUMBER
if ! echo "$PR_URL" | grep -qE '^https://github\.com/[^/]+/[^/]+/pull/[0-9]+'; then
  echo "Error: Invalid GitHub PR URL. Expected: https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

OWNER=$(echo "$PR_URL" | sed -E 's|https://github.com/([^/]+)/.*|\1|')
REPO=$(echo "$PR_URL" | sed -E 's|https://github.com/[^/]+/([^/]+)/.*|\1|')
PR_NUMBER=$(echo "$PR_URL" | sed -E 's|.*/pull/([0-9]+).*|\1|')

echo "Reviewing PR #${PR_NUMBER} in ${OWNER}/${REPO}..."

# ---------------------------------------------------------------------------
# Fetch PR metadata and diff from GitHub API
# ---------------------------------------------------------------------------
GH_HEADERS=(-H "Accept: application/vnd.github+json")
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  GH_HEADERS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

# PR metadata
PR_META=$(curl -sf "${GH_HEADERS[@]}" \
  "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}" 2>/dev/null) || {
  echo "Error: Could not fetch PR metadata. Check the URL and your GITHUB_TOKEN if it's a private repo." >&2
  exit 1
}

PR_TITLE=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['title'])")
PR_BODY=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('body') or '')" | head -50)
BASE_BRANCH=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['base']['ref'])")
HEAD_BRANCH=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['head']['ref'])")
CHANGED_FILES=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['changed_files'])")
ADDITIONS=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['additions'])")
DELETIONS=$(echo "$PR_META" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['deletions'])")

# PR diff
PR_DIFF=$(curl -sf "${GH_HEADERS[@]}" \
  -H "Accept: application/vnd.github.diff" \
  "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}" 2>/dev/null) || {
  echo "Warning: Could not fetch PR diff. Review will be based on metadata only." >&2
  PR_DIFF=""
}

# Truncate diff if too large
if [[ ${#PR_DIFF} -gt $MAX_DIFF_CHARS ]]; then
  echo "Note: Diff is large (${#PR_DIFF} chars), truncating to ${MAX_DIFF_CHARS} chars..."
  PR_DIFF="${PR_DIFF:0:$MAX_DIFF_CHARS}"$'\n\n[... diff truncated for context window ...]'
fi

# ---------------------------------------------------------------------------
# Build Claude prompt
# ---------------------------------------------------------------------------
PROMPT=$(cat <<EOF
You are an expert code reviewer. Review the following GitHub Pull Request and provide a structured Markdown review.

## PR Information
- **Title:** ${PR_TITLE}
- **URL:** ${PR_URL}
- **Branch:** ${HEAD_BRANCH} → ${BASE_BRANCH}
- **Changed files:** ${CHANGED_FILES} | **+${ADDITIONS}** / **-${DELETIONS}**

## PR Description
${PR_BODY}

## Diff
\`\`\`diff
${PR_DIFF}
\`\`\`

---

Provide a review in this exact Markdown format:

## Summary
[2-3 sentences describing what this PR does]

## Risk Assessment: [Low / Medium / High]
[One sentence explaining the risk level and why]

## Identified Risks
- [Risk 1 — specific, actionable]
- [Risk 2]
- [Add more if needed, or write "None identified" if truly safe]

## Improvement Suggestions
- [Suggestion 1 — specific line/pattern if possible]
- [Suggestion 2]
- [Add more or write "None — looks good" if the code is clean]

## Code Quality Notes
- [Note about patterns, naming, test coverage, documentation if relevant]
- [Skip this section if nothing notable]

## Confidence Score: [Low / Medium / High]
[One sentence explaining your confidence — e.g., "High — the diff is small and well-contained" or "Medium — large diff makes it hard to assess all side effects"]

## Verdict
[APPROVE / REQUEST CHANGES / COMMENT] — [one sentence summary of your recommendation]
EOF
)

# ---------------------------------------------------------------------------
# Call Claude API
# ---------------------------------------------------------------------------
echo "Calling Claude API (${MODEL})..."

API_RESPONSE=$(python3 - <<PYEOF
import json, urllib.request, os, sys

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
model = "${MODEL}"
prompt = """${PROMPT}"""

payload = {
    "model": model,
    "max_tokens": 1500,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=json.dumps(payload).encode(),
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(data["content"][0]["text"])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"API Error {e.code}: {body}", file=sys.stderr)
    sys.exit(1)
PYEOF
) || {
  echo "Error: Claude API call failed." >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Format final output
# ---------------------------------------------------------------------------
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HEADER="# PR Review: ${PR_TITLE}

**PR:** [${OWNER}/${REPO}#${PR_NUMBER}](${PR_URL})
**Reviewed:** ${TIMESTAMP}
**Model:** ${MODEL}

---
"

FULL_REVIEW="${HEADER}${API_RESPONSE}"

# Output
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$FULL_REVIEW" > "$OUTPUT_FILE"
  echo "Review saved to: ${OUTPUT_FILE}"
else
  echo ""
  echo "$FULL_REVIEW"
fi
