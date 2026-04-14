#!/usr/bin/env bash
# claude-review: AI-powered PR review agent for Claude Code
# Usage: claude-review --pr <github-pr-url> [--model <model>]
set -euo pipefail

PR_URL=""
MODEL="claude-sonnet-4-20250514"
OUTPUT_FORMAT="markdown"

usage() {
  cat <<EOF
claude-review - AI-powered PR review agent

USAGE:
  claude-review --pr <github-pr-url> [OPTIONS]

OPTIONS:
  --pr <url>       GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
  --model <model>  Claude model to use (default: claude-sonnet-4-20250514)
  --format <fmt>   Output format: markdown|json (default: markdown)
  --output <file>  Write output to file instead of stdout
  -h, --help       Show this help

EXAMPLES:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --model claude-3-5-sonnet
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

REQUIRES:
  - claude CLI (https://docs.anthropic.com/en/docs/claude-code)
  - gh CLI (https://cli.github.com/)
  - ANTHROPIC_API_KEY environment variable
EOF
  exit 0
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pr) PR_URL="$2"; shift 2 ;;
      --model) MODEL="$2"; shift 2 ;;
      --format) OUTPUT_FORMAT="$2"; shift 2 ;;
      --output) OUTPUT_FILE="$2"; shift 2 ;;
      -h|--help) usage ;;
      *) echo "Unknown option: $1"; exit 1 ;;
    esac
  done
}

extract_pr_info() {
  local url="$1"
  # Parse owner/repo and PR number from URL
  if [[ "$url" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    PR_OWNER="${BASH_REMATCH[1]}"
    PR_REPO="${BASH_REMATCH[2]}"
    PR_NUM="${BASH_REMATCH[3]}"
  else
    echo "Error: Invalid GitHub PR URL: $url"
    exit 1
  fi
}

get_pr_diff() {
  echo "Fetching PR diff from $PR_OWNER/$PR_REPO#$PR_NUM..."
  gh pr diff "$PR_NUM" --repo "$PR_OWNER/$PR_REPO" 2>/dev/null || \
    curl -sL "https://api.github.com/repos/$PR_OWNER/$PR_REPO/pulls/$PR_NUM" \
      -H "Accept: application/vnd.github.v3.diff" || {
    echo "Error: Could not fetch PR diff. Make sure gh CLI is authenticated."
    exit 1
  }
}

get_pr_metadata() {
  local pr_json
  pr_json=$(gh pr view "$PR_NUM" --repo "$PR_OWNER/$PR_REPO" --json title,body,author,additions,deletions,changedFiles,baseRefName,headRefName 2>/dev/null)
  if [[ -z "$pr_json" ]]; then
    pr_json=$(curl -sL "https://api.github.com/repos/$PR_OWNER/$PR_REPO/pulls/$PR_NUM")
  fi
  echo "$pr_json"
}

generate_review() {
  local diff="$1"
  local metadata="$2"
  local prompt

  prompt="You are an expert code reviewer. Review this pull request and provide a structured review.

PR Metadata:
$(echo "$metadata" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Title: {d.get(\"title\",\"?\")}'); print(f'Author: {d.get(\"author\",{}).get(\"login\",\"?\")}'); print(f'Base: {d.get(\"baseRefName\",\"?\")} → Head: {d.get(\"headRefName\",\"?\")}'); print(f'Files changed: {d.get(\"changedFiles\",0)}'); print(f'+{d.get(\"additions\",0)} -{d.get(\"deletions\",0)}'); print(f'\\nDescription:\\n{d.get(\"body\",\"No description\")}')")

Diff:
$(echo "$diff" | head -3000)

Provide your review in EXACTLY this format:

## Summary
(2-3 sentences describing what this PR does)

## Risks
- (list each risk on a new line, starting with -)

## Improvement Suggestions
- (list each suggestion on a new line, starting with -)

## Confidence Score
(Medium)

## Details
(Detailed analysis of key changes, potential issues, and recommendations)

IMPORTANT: Be specific. Reference file names and line numbers. Focus on real issues, not style nits."

  if command -v claude &>/dev/null; then
    echo "$prompt" | claude --model "$MODEL" -p 2>/dev/null || \
    claude -p "$prompt" --model "$MODEL" 2>/dev/null
  elif [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    # Fallback: use API directly with curl
    curl -s https://api.anthropic.com/v1/messages \
      -H "x-api-key: $ANTHROPIC_API_KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" \
      -d "$(python3 -c "
import json
prompt = '''$prompt'''
print(json.dumps({
    'model': '$MODEL',
    'max_tokens': 4096,
    'messages': [{'role': 'user', 'content': prompt}]
}))
")" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('content',[{}])[0].get('text','Error: no response'))" 2>/dev/null
  else
    echo "Error: claude CLI or ANTHROPIC_API_KEY required."
    echo "Install claude: https://docs.anthropic.com/en/docs/claude-code"
    echo "Or set ANTHROPIC_API_KEY environment variable."
    exit 1
  fi
}

main() {
  parse_args "$@"
  if [[ -z "$PR_URL" ]]; then
    echo "Error: --pr is required"
    usage
  fi

  extract_pr_info "$PR_URL"
  local diff
  diff=$(get_pr_diff)
  if [[ -z "$diff" ]]; then
    echo "Error: Empty diff"
    exit 1
  fi
  local metadata
  metadata=$(get_pr_metadata)

  echo "Reviewing PR: $PR_OWNER/$PR_REPO#$PR_NUM"
  echo "Model: $MODEL"
  echo "---"

  local review
  review=$(generate_review "$diff" "$metadata")

  if [[ -n "${OUTPUT_FILE:-}" ]]; then
    echo "$review" > "$OUTPUT_FILE"
    echo "Review written to $OUTPUT_FILE"
  else
    echo "$review"
  fi
}

main "$@"
