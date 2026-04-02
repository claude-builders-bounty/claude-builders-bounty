#!/usr/bin/env bash
#
# claude-review — AI-powered PR code review using Claude
#
# Usage:
#   claude-review --pr https://github.com/owner/repo/pull/123
#   claude-review --pr owner/repo#123
#   claude-review --diff ./local.diff
#   claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
#
# Environment:
#   ANTHROPIC_API_KEY   — Required (unless --provider local)
#   GITHUB_TOKEN        — Required for fetching private repos and posting comments
#   CLAUDE_MODEL        — Model to use (default: claude-sonnet-4-20250514)
#   CLAUDE_REVIEW_PROVIDER — "api" (default) or "local" (uses `claude` CLI)
#
set -euo pipefail

# ─── Defaults ────────────────────────────────────────────────────────────────
VERSION="1.2.0"
MODEL="${CLAUDE_MODEL:-claude-sonnet-4-20250514}"
PROVIDER="${CLAUDE_REVIEW_PROVIDER:-api}"
MAX_DIFF_LINES=12000
POST_COMMENT=false
OUTPUT_FILE=""
PR_URL=""
DIFF_FILE=""
VERBOSE=false

# ─── Colors (disabled when not a terminal) ───────────────────────────────────
if [[ -t 2 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

# ─── Helpers ─────────────────────────────────────────────────────────────────
log()  { echo -e "${BLUE}[claude-review]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[warn]${NC} $*" >&2; }
err()  { echo -e "${RED}[error]${NC} $*" >&2; }
ok()   { echo -e "${GREEN}[ok]${NC} $*" >&2; }
die()  { err "$@"; exit 1; }

usage() {
  cat <<'EOF'
claude-review — AI-powered pull request reviewer using Claude

USAGE
  claude-review --pr <url-or-shorthand>  [OPTIONS]
  claude-review --diff <file.diff>       [OPTIONS]

PR FORMATS
  https://github.com/owner/repo/pull/123
  owner/repo#123

OPTIONS
  --pr <url>            GitHub PR URL or owner/repo#number
  --diff <file>         Path to a local .diff / .patch file
  --post-comment        Post the review as a PR comment (requires GITHUB_TOKEN)
  --output <file>       Write Markdown output to a file
  --model <model>       Claude model (default: claude-sonnet-4-20250514)
  --provider <p>        "api" (Anthropic API) or "local" (claude CLI)
  --max-lines <n>       Max diff lines to send (default: 12000)
  --verbose             Show debug output
  --version             Print version and exit
  --help                Show this help

ENVIRONMENT VARIABLES
  ANTHROPIC_API_KEY         Anthropic API key (required for --provider api)
  GITHUB_TOKEN              GitHub token for private repos / posting comments
  CLAUDE_MODEL              Override default model
  CLAUDE_REVIEW_PROVIDER    Override default provider

EXAMPLES
  # Review a public PR, print to stdout
  claude-review --pr https://github.com/astral-sh/ruff/pull/100

  # Review and post as GitHub comment
  claude-review --pr owner/repo#42 --post-comment

  # Review a local diff file
  claude-review --diff changes.diff --output review.md
EOF
  exit 0
}

# ─── Argument parsing ────────────────────────────────────────────────────────
[[ $# -eq 0 ]] && usage

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)           PR_URL="$2"; shift 2 ;;
    --diff)         DIFF_FILE="$2"; shift 2 ;;
    --post-comment) POST_COMMENT=true; shift ;;
    --output)       OUTPUT_FILE="$2"; shift 2 ;;
    --model)        MODEL="$2"; shift 2 ;;
    --provider)     PROVIDER="$2"; shift 2 ;;
    --max-lines)    MAX_DIFF_LINES="$2"; shift 2 ;;
    --verbose)      VERBOSE=true; shift ;;
    --version)      echo "claude-review v${VERSION}"; exit 0 ;;
    --help|-h)      usage ;;
    *)              die "Unknown option: $1. Run with --help for usage." ;;
  esac
done

# ─── Validation ──────────────────────────────────────────────────────────────
[[ -z "$PR_URL" && -z "$DIFF_FILE" ]] && die "Provide --pr <url> or --diff <file>"
[[ -n "$PR_URL" && -n "$DIFF_FILE" ]] && die "Use either --pr or --diff, not both"

if [[ "$PROVIDER" == "api" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  die "ANTHROPIC_API_KEY is required when using --provider api"
fi

if [[ "$PROVIDER" == "local" ]]; then
  command -v claude >/dev/null 2>&1 || die "'claude' CLI not found in PATH"
fi

command -v curl >/dev/null 2>&1 || die "'curl' is required"
command -v jq >/dev/null 2>&1   || die "'jq' is required"

# ─── Parse PR URL ────────────────────────────────────────────────────────────
OWNER="" REPO="" PR_NUMBER="" API_BASE="https://api.github.com"

parse_pr_url() {
  local input="$1"

  # Full URL: https://github.com/owner/repo/pull/123
  if [[ "$input" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
  # Shorthand: owner/repo#123
  elif [[ "$input" =~ ^([^/]+)/([^#]+)#([0-9]+)$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
  else
    die "Cannot parse PR reference: $input\nExpected: https://github.com/owner/repo/pull/123 or owner/repo#123"
  fi

  $VERBOSE && log "Parsed: owner=$OWNER repo=$REPO pr=$PR_NUMBER"
}

# ─── GitHub API helpers ──────────────────────────────────────────────────────
gh_api() {
  local url="$1"
  local accept="${2:-application/vnd.github.v3+json}"
  local response http_code body

  local -a headers=(
    -H "Accept: ${accept}"
    -H "X-GitHub-Api-Version: 2022-11-28"
  )
  [[ -n "${GITHUB_TOKEN:-}" ]] && headers+=(-H "Authorization: Bearer $GITHUB_TOKEN")

  response=$(curl -sS -w "\n%{http_code}" "${headers[@]}" "$url") \
    || die "curl failed for $url"

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [[ "$http_code" -ge 400 ]]; then
    die "GitHub API HTTP $http_code for $url\n$(echo "$body" | jq -r '.message // .' 2>/dev/null | head -5)"
  fi

  echo "$body"
}

# ─── Fetch PR data ──────────────────────────────────────────────────────────
DIFF_CONTENT=""
PR_TITLE="" PR_BODY="" PR_AUTHOR="" PR_BASE="" PR_HEAD=""
FILES_CHANGED="" ADDITIONS=0 DELETIONS=0

fetch_pr_data() {
  local api_url="${API_BASE}/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}"

  log "Fetching PR #${PR_NUMBER} from ${OWNER}/${REPO}..."

  local pr_json
  pr_json=$(gh_api "$api_url")

  PR_TITLE=$(echo "$pr_json" | jq -r '.title // "Untitled"')
  PR_BODY=$(echo "$pr_json" | jq -r '.body // "No description provided."' | head -100)
  PR_AUTHOR=$(echo "$pr_json" | jq -r '.user.login // "unknown"')
  PR_BASE=$(echo "$pr_json" | jq -r '.base.ref // "main"')
  PR_HEAD=$(echo "$pr_json" | jq -r '.head.ref // "unknown"')
  ADDITIONS=$(echo "$pr_json" | jq -r '.additions // 0')
  DELETIONS=$(echo "$pr_json" | jq -r '.deletions // 0')
  FILES_CHANGED=$(echo "$pr_json" | jq -r '.changed_files // 0')

  ok "PR: \"$PR_TITLE\" by @$PR_AUTHOR ($PR_BASE ← $PR_HEAD)"
  log "  $FILES_CHANGED files changed, +$ADDITIONS -$DELETIONS"

  # Fetch diff
  log "Fetching diff..."
  DIFF_CONTENT=$(gh_api "$api_url" "application/vnd.github.v3.diff")

  local diff_lines
  diff_lines=$(echo "$DIFF_CONTENT" | wc -l)
  log "  Diff: $diff_lines lines"

  if [[ "$diff_lines" -gt "$MAX_DIFF_LINES" ]]; then
    warn "Diff is $diff_lines lines (max $MAX_DIFF_LINES). Truncating."
    DIFF_CONTENT=$(echo "$DIFF_CONTENT" | head -n "$MAX_DIFF_LINES")
    DIFF_CONTENT+=$'\n\n[... diff truncated at '"$MAX_DIFF_LINES"' lines ...]'
  fi
}

# ─── Build the review prompt ────────────────────────────────────────────────
build_prompt() {
  local context=""

  if [[ -n "$PR_URL" ]]; then
    context="## Pull Request Context
- **Title**: ${PR_TITLE}
- **Author**: @${PR_AUTHOR}
- **Branch**: \`${PR_HEAD}\` → \`${PR_BASE}\`
- **Stats**: ${FILES_CHANGED} files changed, +${ADDITIONS} −${DELETIONS}

### PR Description
${PR_BODY}

---
"
  fi

  cat <<PROMPT
You are an expert code reviewer. Analyze the following pull request diff and produce a structured review.

${context}
## Diff

\`\`\`diff
${DIFF_CONTENT}
\`\`\`

---

## Instructions

Produce a Markdown review with EXACTLY the following structure. Do not deviate from this format.

### 📝 Summary
Write 2–3 sentences summarizing what this PR does, the approach taken, and the scope of changes.

### ⚠️ Identified Risks
List concrete risks, bugs, or concerns. Each item should reference specific files/lines when possible. If none, write "No significant risks identified."

Format:
- **[Risk Level: High/Medium/Low]** Description — \`file.ext:line\`

### 💡 Suggestions for Improvement
List actionable, specific improvements. Reference files and lines. If the code is already excellent, still offer at least one minor suggestion.

Format:
- Description — \`file.ext:line\` (if applicable)

### 🟢 What Looks Good
Briefly note 1–3 things that are well done (good patterns, test coverage, clean code, etc.).

### 📊 Confidence Score

State your confidence in this review based on how well you understood the code and context:

| Aspect | Rating |
|--------|--------|
| Understanding of changes | High / Medium / Low |
| Risk assessment accuracy | High / Medium / Low |
| **Overall confidence** | **High / Medium / Low** |

> **Reviewer note**: Explain in one sentence what would increase your confidence (e.g., "Access to the full codebase and test results would improve this review.").

---

IMPORTANT RULES:
1. Be specific — reference file names, function names, and line numbers from the diff.
2. Be honest — if the diff is too large or unclear, say so and lower your confidence.
3. Prioritize correctness and security over style.
4. Do NOT suggest trivial style changes unless they impact readability significantly.
5. Output ONLY the Markdown review, no preamble or closing remarks.
PROMPT
}

# ─── Call Claude API ─────────────────────────────────────────────────────────
call_claude_api() {
  local prompt="$1"

  log "Calling Claude API (model: $MODEL)..."

  local escaped_prompt
  escaped_prompt=$(printf '%s' "$prompt" | jq -Rsa .)

  local request_body
  request_body=$(jq -n \
    --arg model "$MODEL" \
    --argjson prompt "$escaped_prompt" \
    '{
      model: $model,
      max_tokens: 4096,
      messages: [{ role: "user", content: $prompt }]
    }')

  local response
  response=$(curl -sS --max-time 120 -X POST "https://api.anthropic.com/v1/messages" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
    -H "anthropic-version: 2023-06-01" \
    -d "$request_body") || die "Failed to call Anthropic API"

  # Check for API errors
  if echo "$response" | jq -e '.type == "error"' >/dev/null 2>&1; then
    local error_msg
    error_msg=$(echo "$response" | jq -r '.error.message // "Unknown API error"')
    die "Anthropic API error: $error_msg"
  fi

  local review
  review=$(echo "$response" | jq -r '.content[0].text // empty')
  [[ -z "$review" ]] && die "Empty response from Claude API.\n$(echo "$response" | jq . 2>/dev/null | head -20)"

  local input_tokens output_tokens
  input_tokens=$(echo "$response" | jq -r '.usage.input_tokens // "?"')
  output_tokens=$(echo "$response" | jq -r '.usage.output_tokens // "?"')
  ok "Response received (tokens: ${input_tokens} in → ${output_tokens} out)"

  echo "$review"
}

# ─── Call Claude CLI (local) ─────────────────────────────────────────────────
call_claude_local() {
  local prompt="$1"

  log "Calling local Claude CLI (model: $MODEL)..."

  local review
  review=$(printf '%s' "$prompt" | claude --model "$MODEL" -p 2>&1) \
    || die "Claude CLI failed"

  ok "Response received from local Claude CLI"
  echo "$review"
}

# ─── Post GitHub comment ────────────────────────────────────────────────────
post_github_comment() {
  local review_body="$1"

  [[ -z "${GITHUB_TOKEN:-}" ]] && die "GITHUB_TOKEN required to post comments"

  local api_url="${API_BASE}/repos/${OWNER}/${REPO}/issues/${PR_NUMBER}/comments"

  local comment_body
  comment_body="## 🤖 Claude Code Review

${review_body}

---
<sub>Generated by <a href=\"https://github.com/\">claude-review</a> v${VERSION} · Model: <code>${MODEL}</code></sub>"

  local escaped_body
  escaped_body=$(printf '%s' "$comment_body" | jq -Rsa .)

  log "Posting review comment to PR #${PR_NUMBER}..."

  local response http_code body
  response=$(curl -sS -w "\n%{http_code}" -X POST "$api_url" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/json" \
    -d "{\"body\": ${escaped_body}}")

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [[ "$http_code" -ge 400 ]]; then
    die "Failed to post comment (HTTP $http_code):\n$(echo "$body" | jq -r '.message // .' 2>/dev/null | head -5)"
  fi

  local comment_url
  comment_url=$(echo "$body" | jq -r '.html_url // "unknown"')
  ok "Comment posted: $comment_url"
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
  log "claude-review v${VERSION}"

  # Get the diff content
  if [[ -n "$PR_URL" ]]; then
    parse_pr_url "$PR_URL"
    fetch_pr_data
  elif [[ -n "$DIFF_FILE" ]]; then
    [[ -f "$DIFF_FILE" ]] || die "Diff file not found: $DIFF_FILE"
    DIFF_CONTENT=$(cat "$DIFF_FILE")
    log "Loaded diff from $DIFF_FILE ($(echo "$DIFF_CONTENT" | wc -l) lines)"
  fi

  [[ -z "$DIFF_CONTENT" ]] && die "No diff content to review"

  # Build the analysis prompt
  local prompt
  prompt=$(build_prompt)
  $VERBOSE && log "Prompt length: $(printf '%s' "$prompt" | wc -c) chars"

  # Call Claude
  local review
  if [[ "$PROVIDER" == "local" ]]; then
    review=$(call_claude_local "$prompt")
  else
    review=$(call_claude_api "$prompt")
  fi

  # Write to file if requested
  if [[ -n "$OUTPUT_FILE" ]]; then
    printf '%s\n' "$review" > "$OUTPUT_FILE"
    ok "Review written to $OUTPUT_FILE"
  fi

  # Post as GitHub comment if requested
  if [[ "$POST_COMMENT" == true && -n "$PR_URL" ]]; then
    post_github_comment "$review"
  fi

  # Always print to stdout
  echo ""
  echo "$review"
}

main