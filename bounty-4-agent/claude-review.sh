#!/usr/bin/env bash
set -euo pipefail

# claude-review: A CLI tool that uses Claude to review GitHub PRs
# Usage: claude-review --pr https://github.com/owner/repo/pull/123 [--post-comment] [--model MODEL]

VERSION="1.0.0"

# --- Defaults ---
POST_COMMENT=false
MODEL="sonnet"
PR_URL=""

# --- Color helpers (disabled if not a terminal) ---
if [ -t 1 ]; then
  BOLD='\033[1m'
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  RESET='\033[0m'
else
  BOLD='' RED='' GREEN='' YELLOW='' RESET=''
fi

usage() {
  cat <<EOF
${BOLD}claude-review${RESET} v${VERSION}

AI-powered pull request reviewer using Claude.

${BOLD}USAGE${RESET}
  claude-review --pr <PR_URL> [OPTIONS]

${BOLD}OPTIONS${RESET}
  --pr <URL>          GitHub PR URL (required)
                      e.g. https://github.com/owner/repo/pull/123
  --post-comment      Post the review as a PR comment (default: stdout only)
  --model <MODEL>     Claude model to use (default: sonnet)
  --help              Show this help message
  --version           Show version

${BOLD}PREREQUISITES${RESET}
  - gh (GitHub CLI) authenticated
  - claude (Claude Code CLI) installed

${BOLD}EXAMPLES${RESET}
  claude-review --pr https://github.com/facebook/react/pull/28000
  claude-review --pr https://github.com/owner/repo/pull/42 --post-comment
EOF
  exit 0
}

die() {
  echo -e "${RED}Error:${RESET} $1" >&2
  exit 1
}

info() {
  echo -e "${GREEN}>>>${RESET} $1" >&2
}

warn() {
  echo -e "${YELLOW}Warning:${RESET} $1" >&2
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)
      PR_URL="$2"
      shift 2
      ;;
    --post-comment)
      POST_COMMENT=true
      shift
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    --version|-v)
      echo "claude-review v${VERSION}"
      exit 0
      ;;
    *)
      die "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

# --- Validate ---
[[ -z "$PR_URL" ]] && die "Missing --pr flag. Usage: claude-review --pr <PR_URL>"

# Parse PR URL: https://github.com/owner/repo/pull/123
if [[ "$PR_URL" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR_NUMBER="${BASH_REMATCH[2]}"
else
  die "Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123"
fi

# Check prerequisites
command -v gh >/dev/null 2>&1 || die "GitHub CLI (gh) is not installed. Install: https://cli.github.com"
command -v claude >/dev/null 2>&1 || die "Claude Code CLI is not installed. Install: https://docs.anthropic.com/en/docs/claude-code"

info "Reviewing PR #${PR_NUMBER} in ${REPO}..."

# --- Fetch PR data ---
info "Fetching PR metadata..."
PR_META=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json title,body,additions,deletions,changedFiles,baseRefName,headRefName,files,labels,author 2>&1) \
  || die "Failed to fetch PR metadata. Check that the PR exists and gh is authenticated."

info "Fetching PR diff..."
PR_DIFF=$(gh pr diff "$PR_NUMBER" --repo "$REPO" 2>&1) \
  || die "Failed to fetch PR diff."

# Calculate diff stats for the prompt
DIFF_LINES=$(echo "$PR_DIFF" | wc -l | tr -d ' ')
ADDITIONS=$(echo "$PR_META" | jq -r '.additions // 0')
DELETIONS=$(echo "$PR_META" | jq -r '.deletions // 0')
CHANGED_FILES=$(echo "$PR_META" | jq -r '.changedFiles // 0')
PR_TITLE=$(echo "$PR_META" | jq -r '.title // "Untitled"')
PR_BODY=$(echo "$PR_META" | jq -r '.body // "No description provided."')
PR_AUTHOR=$(echo "$PR_META" | jq -r '.author.login // "unknown"')
BASE_BRANCH=$(echo "$PR_META" | jq -r '.baseRefName // "main"')
HEAD_BRANCH=$(echo "$PR_META" | jq -r '.headRefName // "unknown"')
FILES_LIST=$(echo "$PR_META" | jq -r '.files[].path' 2>/dev/null | head -100)

# Truncate very large diffs to avoid exceeding context limits
MAX_DIFF_LINES=8000
if [[ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]]; then
  warn "Diff is ${DIFF_LINES} lines, truncating to ${MAX_DIFF_LINES} lines for review."
  PR_DIFF=$(echo "$PR_DIFF" | head -n "$MAX_DIFF_LINES")
  TRUNCATED_NOTE="NOTE: The diff was truncated from ${DIFF_LINES} to ${MAX_DIFF_LINES} lines. Some files may not be fully reviewed."
else
  TRUNCATED_NOTE=""
fi

info "PR: \"${PR_TITLE}\" by ${PR_AUTHOR} (+${ADDITIONS}/-${DELETIONS}, ${CHANGED_FILES} files)"

# --- Build the review prompt ---
REVIEW_PROMPT=$(cat <<'PROMPT_EOF'
You are a senior software engineer performing a thorough code review of a GitHub pull request. Analyze the PR metadata and diff provided below, then produce a structured review.

## Your Review Methodology

1. **Understand Intent**: Read the PR title, description, and branch names to understand the goal.
2. **Analyze Changes**: Examine every file change in the diff carefully.
3. **Assess Risk**: Consider security vulnerabilities, performance regressions, correctness issues, edge cases, backwards compatibility, error handling gaps, and race conditions.
4. **Suggest Improvements**: Provide actionable, specific suggestions — reference file names and line numbers where possible.
5. **Calibrate Confidence**: Base your confidence on how much of the change you can fully understand from the diff alone.

## Review Focus Areas

- **Security**: SQL injection, XSS, CSRF, auth bypasses, secrets in code, insecure defaults, input validation
- **Performance**: N+1 queries, unnecessary re-renders, missing indexes, unbounded loops, memory leaks, large allocations
- **Correctness**: Off-by-one errors, null/undefined handling, race conditions, incorrect logic, missing error handling
- **Compatibility**: Breaking API changes, migration issues, deprecated APIs, browser/runtime compatibility
- **Code Quality**: Dead code, code duplication, unclear naming, missing types, overly complex logic
- **Testing**: Missing test coverage for new logic, untested edge cases, brittle tests
- **Documentation**: Missing or outdated comments, changelog entries, API docs

## Output Format

Produce ONLY the following Markdown structure, nothing else:

---

## PR Review: {PR_TITLE}

**PR**: #{PR_NUMBER} | **Author**: {AUTHOR} | **Branch**: `{HEAD}` -> `{BASE}`
**Changes**: +{ADDITIONS}/-{DELETIONS} across {CHANGED_FILES} files

### Summary

{2-3 sentence overview of what this PR does and its approach. Be specific about the actual changes, not generic.}

### Risk Assessment

| Risk | Severity | Details |
|------|----------|---------|
| {risk name} | {Critical/High/Medium/Low} | {specific explanation with file/line references} |

{If no significant risks found, state: "No significant risks identified in this change."}

### Suggestions

{Numbered list of actionable improvement suggestions. Each should reference specific files/lines and explain both the issue and the fix. If the code is solid, say so and optionally suggest minor polish.}

1. **{Short title}** (`{file}`)
   {Detailed explanation of the suggestion.}

2. ...

### What Looks Good

{Brief list of things done well — good patterns, solid error handling, clean abstractions, etc.}

### Confidence

**{Low|Medium|High}**

{One sentence justifying the confidence level. Consider: diff size, domain complexity, whether tests are included, whether you can see the full picture from the diff alone.}

---
PROMPT_EOF
)

# --- Compose the full input for Claude ---
CLAUDE_INPUT=$(cat <<EOF
# Pull Request Review Request

## PR Metadata
- **Title**: ${PR_TITLE}
- **Author**: ${PR_AUTHOR}
- **PR Number**: #${PR_NUMBER}
- **Repository**: ${REPO}
- **Branch**: \`${HEAD_BRANCH}\` -> \`${BASE_BRANCH}\`
- **Stats**: +${ADDITIONS}/-${DELETIONS} across ${CHANGED_FILES} files

## PR Description
${PR_BODY}

## Changed Files
${FILES_LIST}

${TRUNCATED_NOTE}

## Diff
\`\`\`diff
${PR_DIFF}
\`\`\`
EOF
)

# --- Run Claude ---
info "Running Claude review (model: ${MODEL})..."

REVIEW_OUTPUT=$(echo "$CLAUDE_INPUT" | claude --model "$MODEL" --print --no-input "$REVIEW_PROMPT" 2>&1) \
  || die "Claude review failed. Check that the claude CLI is working."

# --- Output ---
echo ""
echo "$REVIEW_OUTPUT"

# --- Optionally post as PR comment ---
if [[ "$POST_COMMENT" == "true" ]]; then
  info "Posting review as PR comment..."

  COMMENT_BODY=$(cat <<EOF
<!-- claude-review-bot -->
> *This review was generated by [claude-review](https://github.com/opire/claude-builders-bounty/tree/bounty-4-pr-review-agent/bounty-4-agent) using Claude.*

${REVIEW_OUTPUT}
EOF
)

  echo "$COMMENT_BODY" | gh pr comment "$PR_NUMBER" --repo "$REPO" --body-file - \
    && info "Review posted as comment on PR #${PR_NUMBER}." \
    || warn "Failed to post comment. Review was printed above."
fi
