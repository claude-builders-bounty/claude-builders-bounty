#!/usr/bin/env bash
# review.sh — Core review logic for claude-review
# Sourced by the CLI entry point and the GitHub Action.

set -euo pipefail

# ── Globals set by parse_pr_url ──────────────────────────────────────────────
OWNER=""
REPO=""
PR_NUMBER=""

# ── Logging helpers ──────────────────────────────────────────────────────────
log()  { echo >&2 "[claude-review] $*"; }
err()  { echo >&2 "[claude-review] ERROR: $*"; }

# ── Dependency check ─────────────────────────────────────────────────────────
check_dependencies() {
  local missing=()
  command -v gh      >/dev/null 2>&1 || missing+=("gh (GitHub CLI)")
  command -v claude  >/dev/null 2>&1 || missing+=("claude (Claude Code CLI)")

  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools:"
    for tool in "${missing[@]}"; do
      err "  - $tool"
    done
    exit 1
  fi

  # Verify gh is authenticated
  if ! gh auth status >/dev/null 2>&1; then
    err "GitHub CLI is not authenticated. Run: gh auth login"
    exit 1
  fi
}

# ── URL parser ───────────────────────────────────────────────────────────────
parse_pr_url() {
  local url="$1"

  # Accept: https://github.com/owner/repo/pull/123
  if [[ "$url" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
  else
    err "Invalid PR URL format: $url"
    err "Expected: https://github.com/owner/repo/pull/123"
    exit 1
  fi
}

# ── Fetch PR data ────────────────────────────────────────────────────────────
fetch_pr_metadata() {
  local owner="$1" repo="$2" number="$3"
  gh pr view "$number" --repo "${owner}/${repo}" \
    --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,files \
    2>/dev/null
}

fetch_pr_diff() {
  local owner="$1" repo="$2" number="$3"
  gh pr diff "$number" --repo "${owner}/${repo}" 2>/dev/null
}

# ── Truncate diff if too large ───────────────────────────────────────────────
truncate_diff() {
  local diff="$1"
  local max_lines=1500
  local line_count
  line_count="$(echo "$diff" | wc -l)"

  if [[ "$line_count" -gt "$max_lines" ]]; then
    echo "$diff" | head -n "$max_lines"
    echo ""
    echo "[... diff truncated: ${line_count} total lines, showing first ${max_lines} ...]"
  else
    echo "$diff"
  fi
}

# ── Build prompt ─────────────────────────────────────────────────────────────
build_review_prompt() {
  local metadata="$1" diff="$2"

  cat <<PROMPT
You are an expert code reviewer. Analyze the following GitHub pull request and provide a structured review.

## PR Metadata
\`\`\`json
${metadata}
\`\`\`

## PR Diff
\`\`\`diff
${diff}
\`\`\`

## Instructions
Produce your review in EXACTLY this Markdown format — no extra sections, no wrapping fences:

## Summary
<2-3 sentence summary of what this PR does and why>

## Risks
<bulleted list of identified risks, security concerns, or potential issues. If none, say "No significant risks identified.">

## Suggestions
<bulleted list of concrete improvement suggestions. If the code looks good, say "No major suggestions — code looks solid.">

## Confidence
<exactly one of: **Low**, **Medium**, or **High**>

<1 sentence justification for the confidence score>

---
*Automated review by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)*
PROMPT
}

# ── Run the review ───────────────────────────────────────────────────────────
run_review() {
  local owner="$1" repo="$2" number="$3"

  log "Fetching PR #${number} from ${owner}/${repo}..."

  local metadata diff

  metadata="$(fetch_pr_metadata "$owner" "$repo" "$number")" || {
    err "Failed to fetch PR metadata. Check the URL and your gh authentication."
    exit 1
  }

  diff="$(fetch_pr_diff "$owner" "$repo" "$number")" || {
    err "Failed to fetch PR diff."
    exit 1
  }

  if [[ -z "$diff" ]]; then
    err "PR diff is empty — nothing to review."
    exit 1
  fi

  diff="$(truncate_diff "$diff")"

  log "Generating review with Claude..."

  local prompt
  prompt="$(build_review_prompt "$metadata" "$diff")"

  local review
  review="$(echo "$prompt" | claude -p --output-format text 2>/dev/null)" || {
    err "Claude CLI failed. Make sure 'claude' is installed and working."
    exit 1
  }

  echo "$review"
}
