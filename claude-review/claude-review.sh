#!/usr/bin/env bash
set -euo pipefail

# claude-review — PR Review Agent for Claude Code
# Usage: claude-review --pr <pr-url> [--output <file>] [--format <format>]
#        claude-review --diff <diff-file>
#        claude-review --help

VERSION="1.0.0"

usage() {
  cat <<EOF
Usage:
  claude-review --pr <pr-url>       Review a GitHub PR by URL
  claude-review --diff <file>       Review a local diff file
  claude-review --gh <pr-number>    Review PR in the current repo (uses gh CLI)
  claude-review --help              Show this help message
  claude-review --version           Show version

Options:
  --output <file>   Write output to file (default: stdout)
  --format <fmt>    Output format: markdown (default), json, plain

Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --gh 42
  claude-review --diff /tmp/changes.diff
EOF
  exit 0
}

# ── Argument parsing ──────────────────────────────────────────────
PR_URL=""
DIFF_FILE=""
OUTPUT_FILE=""
OUTPUT_FORMAT="markdown"
GH_PR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)      PR_URL="$2"; shift 2 ;;
    --diff)    DIFF_FILE="$2"; shift 2 ;;
    --gh)      GH_PR="$2"; shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    --format)  OUTPUT_FORMAT="$2"; shift 2 ;;
    --help)    usage ;;
    --version) echo "claude-review v${VERSION}"; exit 0 ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# ── Fetch diff ────────────────────────────────────────────────────
DIFF_CONTENT=""

if [[ -n "$PR_URL" ]]; then
  # Convert PR URL to diff URL
  DIFF_URL="${PR_url%/}/files"
  API_URL="${PR_URL/github.com/api.github.com/repos}"
  API_URL="${API_URL/pull/pulls}"
  echo "Fetching PR diff..." >&2
  DIFF_CONTENT=$(curl -sL -H "Accept: application/vnd.github.v3.diff" "$PR_URL.diff" 2>/dev/null || true)
  if [[ -z "$DIFF_CONTENT" ]]; then
    echo "Error: Could not fetch PR diff. Check the URL or network." >&2
    exit 1
  fi
elif [[ -n "$GH_PR" ]]; then
  echo "Fetching PR #$GH_PR via gh CLI..." >&2
  DIFF_CONTENT=$(gh pr view "$GH_PR" --json body --jq ".body" 2>/dev/null || true)
  if [[ -z "$DIFF_CONTENT" ]]; then
    echo "Error: Could not fetch PR #$GH_PR. Is gh installed and authenticated?" >&2
    exit 1
  fi
elif [[ -n "$DIFF_FILE" ]]; then
  echo "Reading diff from file..." >&2
  if [[ ! -f "$DIFF_FILE" ]]; then
    echo "Error: File not found: $DIFF_FILE" >&2
    exit 1
  fi
  DIFF_CONTENT=$(cat "$DIFF_FILE")
else
  echo "Error: Specify --pr, --gh, or --diff" >&2
  usage
fi

# ── Generate review ────────────────────────────────────────────────
# This script prepares the diff for Claude Code to analyze.
# The actual analysis is done by Claude Code via the AGENT.md prompt.
# Here we just fetch, format, and output.

if [[ -n "$OUTPUT_FILE" ]]; then
  # Save diff to file for Claude Code to analyze
  echo "$DIFF_CONTENT" > "$OUTPUT_FILE.diff"
  echo "Diff saved to: $OUTPUT_FILE.diff" >&2
  echo "Now run: claude --agent AGENT.md -p \"Review the changes in $OUTPUT_FILE.diff\"" >&2
else
  # Output the diff for piping into Claude Code
  echo "$DIFF_CONTENT"
fi
