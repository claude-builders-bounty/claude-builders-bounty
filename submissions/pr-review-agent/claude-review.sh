#!/usr/bin/env bash
# claude-review — Claude Code sub-agent that reviews a PR and posts structured comments
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
#        gh pr view 123 --json body,title,additions,deletions,files,changedFiles | claude-review --stdin
set -euo pipefail

OUTPUT=""

# ── Parse arguments ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR_URL="$2"
      shift 2
      ;;
    --stdin)
      READ_FROM_STDIN=true
      shift
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: claude-review --pr <pr-url> [--output <file>]"
      echo "       gh pr view <number> --json body,title,... | claude-review --stdin"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────
red()   { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow(){ echo -e "\033[33m$1\033[0m"; }
bold()  { echo -e "\033[1m$1\033[0m"; }

# ── Fetch PR information ─────────────────────────────────────────
if [[ -n "${PR_URL:-}" ]]; then
  if ! echo "$PR_URL" | grep -qE 'github\.com/.+/.+/pull/[0-9]+'; then
    echo "Error: invalid PR URL. Expected: https://github.com/owner/repo/pull/123" >&2
    exit 1
  fi

  OWNER=$(echo "$PR_URL" | sed -E 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1|')
  REPO=$(echo "$PR_URL" | sed -E 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\2|')
  PR_NUM=$(echo "$PR_URL" | sed -E 's|https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\3|')
  REPO_FULL="${OWNER}/${REPO}"

  echo "🔍 Reviewing $REPO_FULL#$PR_NUM ..." >&2

  PR_DATA=$(gh pr view "$PR_NUM" --repo "$REPO_FULL" --json title,body,state,mergeable,additions,deletions,author,files,headRefName,baseRefName,createdAt,labels,reviews 2>/dev/null || true)
  PR_DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO_FULL" 2>/dev/null || true)

elif [[ "${READ_FROM_STDIN:-}" == "true" ]]; then
  PR_DATA=$(cat)
  PR_NUM=$(echo "$PR_DATA" | jq -r '.number // "unknown"')
  REPO_FULL=$(echo "$PR_DATA" | jq -r '.repository // "unknown"')
  PR_DIFF=""
else
  echo "Error: provide --pr <url> or --stdin" >&2
  exit 1
fi

if [[ -z "$PR_DATA" || "$PR_DATA" == "null" ]]; then
  echo "Error: could not fetch PR data. Check your gh CLI authentication." >&2
  exit 1
fi

# ── Parse PR data ────────────────────────────────────────────────
TITLE=$(echo "$PR_DATA" | jq -r '.title // "Untitled"')
BODY=$(echo "$PR_DATA" | jq -r '.body // ""')
STATE=$(echo "$PR_DATA" | jq -r '.state // "unknown"')
ADDITIONS=$(echo "$PR_DATA" | jq -r '.additions // 0')
DELETIONS=$(echo "$PR_DATA" | jq -r '.deletions // 0')
CHANGED_FILES=$(echo "$PR_DATA" | jq -r '.files // [] | length')
AUTHOR=$(echo "$PR_DATA" | jq -r '.author.login // "unknown"')
HEAD_BRANCH=$(echo "$PR_DATA" | jq -r '.headRefName // "unknown"')
BASE_BRANCH=$(echo "$PR_DATA" | jq -r '.baseRefName // "unknown"')
CREATED_AT=$(echo "$PR_DATA" | jq -r '.createdAt // "unknown"')
REVIEW_STATE=$(echo "$PR_DATA" | jq -r '[.reviews[]?.state] | join(", ") // "none"')

FILE_LIST=$(echo "$PR_DATA" | jq -r '.files[]?.path // empty')

# ── Fetch diff if not already got ────────────────────────────────
if [[ -z "$PR_DIFF" && -n "${PR_URL:-}" ]]; then
  PR_DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO_FULL" 2>/dev/null || true)
fi

# ── Static analysis ──────────────────────────────────────────────
declare -a RISKS=()
declare -a SUGGESTIONS=()

# Check for common issues in the diff
if [[ -n "$PR_DIFF" ]]; then
  # Hardcoded secrets / credentials
  if echo "$PR_DIFF" | grep -qE '(\bAKIA[0-9A-Z]{16}\b|sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36})'; then
    RISKS+=("Potential credential leak detected (API key, token, or secret in diff)")
  fi

  # Debug code
  if echo "$PR_DIFF" | grep -qE '^\+\s*(console\.log|println!|print|pdb\.set_trace|debugger|var_dump|dd\()' && \
     ! echo "$PR_DIFF" | head -30 | grep -qi "test\|debug\|wip"; then
    SUGGESTIONS+=("Remove debug statements (console.log, println, etc.) before merging")
  fi

  # TODO/FIXME left in code
  if echo "$PR_DIFF" | grep -qE '^\+\s*.*\b(TODO|FIXME|HACK|XXX)\b'; then
    SUGGESTIONS+=("Address remaining TODO/FIXME/HACK comments in the diff")
  fi

  # Large files
  if echo "$PR_DIFF" | grep -qE '^\+\s*.{200,}'; then
    SUGGESTIONS+=("Consider breaking long lines (>200 chars) for readability")
  fi

  # Missing error handling
  if echo "$PR_DIFF" | grep -qE '^\+\s*(await|fetch|axios|request|\.call|\.invoke)\b' && \
     ! echo "$PR_DIFF" | grep -qE '^\+\s*.*\.catch\b|^\+\s*.*try\s*\{|^\+\s*.*except'; then
    SUGGESTIONS+=("Some async operations appear to lack error handling (try/catch or .catch)")
  fi

  # TypeScript any type
  if echo "$PR_DIFF" | grep -qE '^\+\s*.*:\s*any\b'; then
    SUGGESTIONS+=("Using `any` type — consider using `unknown` or a proper type instead")
  fi

  # Console.log in JavaScript/TypeScript
  if echo "$PR_DIFF" | grep -qE '^\+\s*console\.log\('; then
    SUGGESTIONS+=("Remove console.log() calls (use a proper logger or remove before merging)")
  fi
fi

# ── Calculate confidence score ───────────────────────────────────
RISK_COUNT=${#RISKS[@]}
SUGGESTION_COUNT=${#SUGGESTIONS[@]}
OVERALL_SCORE="High"

if [[ "$CHANGED_FILES" -gt 20 ]]; then
  OVERALL_SCORE="Medium"
fi
if [[ "$RISK_COUNT" -gt 2 ]]; then
  OVERALL_SCORE="Low"
fi
if [[ "$ADDITIONS" -gt 1000 ]]; then
  OVERALL_SCORE="Low"
fi

# ── Summary generation ───────────────────────────────────────────
SUMMARY=$(cat <<EOF
This PR (by **@${AUTHOR}**) makes **${ADDITIONS} additions** and **${DELETIONS} deletions** across **${CHANGED_FILES} files** in the \`${HEAD_BRANCH}\` branch, targeting \`${BASE_BRANCH}\`.
EOF
)

if [[ "$CHANGED_FILES" -le 3 && "$ADDITIONS" -le 100 ]]; then
  SUMMARY="$SUMMARY It is a small, focused change."
elif [[ "$CHANGED_FILES" -le 10 && "$ADDITIONS" -le 500 ]]; then
  SUMMARY="$SUMMARY It is a moderate-sized change."
else
  SUMMARY="$SUMMARY It is a large change — consider breaking it into smaller PRs for faster review."
fi

# ── Output ───────────────────────────────────────────────────────
OUTPUT_TEXT=""

OUTPUT_TEXT+="$(bold "# 🔍 PR Review: ${TITLE}")"$'\n\n'

OUTPUT_TEXT+="$(bold "## Summary")"$'\n'
OUTPUT_TEXT+="${SUMMARY}"$'\n\n'

OUTPUT_TEXT+="$(bold "## Details")"$'\n'
OUTPUT_TEXT+="| Field | Value |"$'\n'
OUTPUT_TEXT+="|-------|-------|"$'\n'
OUTPUT_TEXT+="| PR # | ${PR_NUM} |"$'\n'
OUTPUT_TEXT+="| State | ${STATE} |"$'\n'
OUTPUT_TEXT+="| Author | @${AUTHOR} |"$'\n'
OUTPUT_TEXT+="| Base → Head | ${BASE_BRANCH} → ${HEAD_BRANCH} |"$'\n'
OUTPUT_TEXT+="| Files changed | ${CHANGED_FILES} |"$'\n'
OUTPUT_TEXT+="| Additions | ${ADDITIONS} |"$'\n'
OUTPUT_TEXT+="| Deletions | ${DELETIONS} |"$'\n'
OUTPUT_TEXT+="| Created | ${CREATED_AT} |"$'\n'
OUTPUT_TEXT+="| Reviews | ${REVIEW_STATE} |"$'\n'
OUTPUT_TEXT+=""$'\n'

if [[ -n "${RISKS[*]:-}" ]]; then
  OUTPUT_TEXT+="$(red "$(bold "## 🚨 Identified Risks")")"$'\n'
  for i in "${!RISKS[@]}"; do
    OUTPUT_TEXT+="- ⚠️ ${RISKS[$i]}"$'\n'
  done
  OUTPUT_TEXT+=""$'\n'
else
  OUTPUT_TEXT+="$(green "$(bold "## ✅ No Critical Risks Identified")")"$'\n'
  OUTPUT_TEXT+="No obvious security or correctness issues detected by static analysis."$'\n'
  OUTPUT_TEXT+=""$'\n'
fi

if [[ -n "${SUGGESTIONS[*]:-}" ]]; then
  OUTPUT_TEXT+="$(yellow "$(bold "## 💡 Improvement Suggestions")")"$'\n'
  for i in "${!SUGGESTIONS[@]}"; do
    OUTPUT_TEXT+="- **${SUGGESTIONS[$i]}**"$'\n'
  done
  OUTPUT_TEXT+=""$'\n'
fi

OUTPUT_TEXT+="$(bold "## Confidence Score")"$'\n'
case "$OVERALL_SCORE" in
  High)   OUTPUT_TEXT+="**High** 🟢 — Review is based on reliable static analysis with clear findings." ;;
  Medium) OUTPUT_TEXT+="**Medium** 🟡 — Large PR size limits confidence; manual review recommended for complex areas." ;;
  Low)    OUTPUT_TEXT+="**Low** 🔴 — PR is very large or has multiple risks; thorough manual review strongly recommended." ;;
esac
OUTPUT_TEXT+=""$'\n\n'

OUTPUT_TEXT+="---"$'\n'
OUTPUT_TEXT+="*Reviewed by claude-review · $(date +%Y-%m-%d\ %H:%M:%S)*"$'\n'

if [[ -n "$OUTPUT" ]]; then
  echo "$OUTPUT_TEXT" > "$OUTPUT"
  echo "✓ Review written to $OUTPUT" >&2
else
  echo "$OUTPUT_TEXT"
fi
