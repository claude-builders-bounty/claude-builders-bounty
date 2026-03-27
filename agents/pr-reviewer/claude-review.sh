#!/usr/bin/env bash
# claude-review -- Claude Code PR Reviewer Agent
# Analyzes a GitHub pull request and produces structured Markdown review output.
#
# Usage:
#   claude-review --pr https://github.com/owner/repo/pull/123
#   claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
#
# Requirements:
#   - gh (GitHub CLI, authenticated)
#   - claude (Claude Code CLI)
#
# Part of claude-builders-bounty (Bounty #4)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_TEMPLATE="${SCRIPT_DIR}/review-prompt.md"

# ------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------
PR_URL=""
OUTPUT_FILE=""
VERBOSE=0

# ------------------------------------------------------------------
# Usage
# ------------------------------------------------------------------
usage() {
  cat <<'HELP'
claude-review -- Claude Code PR Reviewer Agent

USAGE
  claude-review --pr <PR_URL> [OPTIONS]

OPTIONS
  --pr <url>        GitHub pull request URL (required)
  --output <file>   Write review to file instead of stdout
  --verbose         Show progress messages on stderr
  --help            Show this help message

EXAMPLES
  claude-review --pr https://github.com/owner/repo/pull/42
  claude-review --pr https://github.com/owner/repo/pull/42 --output review.md
  claude-review --pr https://github.com/owner/repo/pull/42 --verbose
HELP
  exit 0
}

# ------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR_URL="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "Error: Unknown option '$1'" >&2
      echo "Run 'claude-review --help' for usage." >&2
      exit 1
      ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr <URL> is required." >&2
  echo "Run 'claude-review --help' for usage." >&2
  exit 1
fi

# ------------------------------------------------------------------
# Validate dependencies
# ------------------------------------------------------------------
for cmd in gh claude; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: '$cmd' is not installed or not in PATH." >&2
    exit 1
  fi
done

# ------------------------------------------------------------------
# Extract owner/repo and PR number from the URL
# ------------------------------------------------------------------
if [[ "$PR_URL" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUMBER="${BASH_REMATCH[2]}"
else
  echo "Error: Could not parse PR URL. Expected format: https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

log() {
  if [[ "$VERBOSE" -eq 1 ]]; then
    echo "[claude-review] $*" >&2
  fi
}

# ------------------------------------------------------------------
# Fetch PR metadata and diff
# ------------------------------------------------------------------
log "Fetching PR #${PR_NUMBER} from ${REPO}..."

PR_TITLE="$(gh pr view "$PR_NUMBER" --repo "$REPO" --json title --jq '.title' 2>/dev/null)" || {
  echo "Error: Could not fetch PR title. Check the URL and your gh auth status." >&2
  exit 1
}

PR_AUTHOR="$(gh pr view "$PR_NUMBER" --repo "$REPO" --json author --jq '.author.login' 2>/dev/null)" || PR_AUTHOR="unknown"

PR_BODY="$(gh pr view "$PR_NUMBER" --repo "$REPO" --json body --jq '.body' 2>/dev/null)" || PR_BODY="(no description)"

# Handle empty/null PR body
if [[ -z "$PR_BODY" || "$PR_BODY" == "null" ]]; then
  PR_BODY="(no description provided)"
fi

log "Title: ${PR_TITLE}"
log "Author: ${PR_AUTHOR}"
log "Fetching diff..."

PR_DIFF="$(gh pr diff "$PR_NUMBER" --repo "$REPO" 2>/dev/null)" || {
  echo "Error: Could not fetch PR diff." >&2
  exit 1
}

DIFF_LINES="$(echo "$PR_DIFF" | wc -l)"
log "Diff size: ${DIFF_LINES} lines"

# Truncate extremely large diffs to avoid token limits
MAX_DIFF_LINES=3000
if [[ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]]; then
  log "Warning: Diff exceeds ${MAX_DIFF_LINES} lines. Truncating for review."
  PR_DIFF="$(echo "$PR_DIFF" | head -n "$MAX_DIFF_LINES")"
  PR_DIFF="${PR_DIFF}

... [diff truncated at ${MAX_DIFF_LINES} lines -- review may be incomplete]"
fi

# ------------------------------------------------------------------
# Build the prompt from template
# ------------------------------------------------------------------
log "Building review prompt..."

TODAY="$(date +%Y-%m-%d)"

if [[ -f "$PROMPT_TEMPLATE" ]]; then
  PROMPT="$(cat "$PROMPT_TEMPLATE")"
else
  # Fallback inline prompt if template file is missing
  PROMPT="You are a senior code reviewer. Review this PR and produce structured Markdown output with: Summary (2-3 sentences), Identified Risks (bullet list), Improvement Suggestions (bullet list with file/line refs), File-by-File Notes (table), and Confidence Score (Low/Medium/High with explanation).

PR Title: {{PR_TITLE}}
PR Author: {{PR_AUTHOR}}
PR URL: {{PR_URL}}

Description:
{{PR_BODY}}

Diff:
{{PR_DIFF}}"
fi

# Replace template variables
PROMPT="${PROMPT//\{\{PR_TITLE\}\}/$PR_TITLE}"
PROMPT="${PROMPT//\{\{PR_AUTHOR\}\}/$PR_AUTHOR}"
PROMPT="${PROMPT//\{\{PR_URL\}\}/$PR_URL}"
PROMPT="${PROMPT//\{\{DATE\}\}/$TODAY}"
PROMPT="${PROMPT//\{\{PR_BODY\}\}/$PR_BODY}"
PROMPT="${PROMPT//\{\{PR_DIFF\}\}/$PR_DIFF}"

# ------------------------------------------------------------------
# Send to Claude Code for review
# ------------------------------------------------------------------
log "Sending to Claude Code for analysis..."

REVIEW="$(echo "$PROMPT" | claude --print 2>/dev/null)" || {
  echo "Error: Claude Code returned an error. Ensure 'claude' CLI is installed and configured." >&2
  exit 1
}

# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REVIEW" > "$OUTPUT_FILE"
  log "Review written to ${OUTPUT_FILE}"
  echo "Review saved to: ${OUTPUT_FILE}" >&2
else
  echo "$REVIEW"
fi
