#!/usr/bin/env bash
# claude-review.sh — Review a GitHub PR and post a structured comment
# Usage: ./claude-review.sh <PR_URL> [--post]
#   --post  Actually post the review as a GitHub comment (requires GH_TOKEN)
#   Without --post, prints review to stdout
#
# Prerequisites: curl, jq, gh (GitHub CLI) if --post is used
# Env: GH_TOKEN or GITHUB_TOKEN for authentication

set -euo pipefail

PR_URL="${1:?Usage: claude-review.sh <PR_URL> [--post]}"
POST_COMMENT=false
[[ "${2:-}" == "--post" ]] && POST_COMMENT=true

# --- Parse PR URL ---
# Supports: https://github.com/owner/repo/pull/123
OWNER_REPO=$(echo "$PR_URL" | sed -E 's|https://github.com/([^/]+/[^/]+)/pull/[0-9]+|\1|')
PR_NUM=$(echo "$PR_URL" | sed -E 's|https://github.com/[^/]+/[^/]+/pull/([0-9]+)|\1|')

if [[ -z "$OWNER_REPO" || -z "$PR_NUM" || "$OWNER_REPO" == "$PR_URL" ]]; then
  echo "Error: Invalid PR URL. Expected format: https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
AUTH_HEADER=""
if [[ -n "$TOKEN" ]]; then
  AUTH_HEADER="Authorization: token $TOKEN"
fi

# --- Fetch PR data ---
PR_DATA=$(curl -s -H "$AUTH_HEADER" "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM")
TITLE=$(echo "$PR_DATA" | jq -r '.title')
BODY=$(echo "$PR_DATA" | jq -r '.body // "(no description)"')
ADDED=$(echo "$PR_DATA" | jq -r '.additions // 0')
DELETED=$(echo "$PR_DATA" | jq -r '.deletions // 0')
CHANGED_FILES=$(echo "$PR_DATA" | jq -r '.changed_files // 0')
STATE=$(echo "$PR_DATA" | jq -r '.state // ""')
MERGEABLE=$(echo "$PR_DATA" | jq -r '.mergeable // "unknown"')
BASE=$(echo "$PR_DATA" | jq -r '.base.ref // "unknown"')
HEAD=$(echo "$PR_DATA" | jq -r '.head.ref // "unknown"')
AUTHOR=$(echo "$PR_DATA" | jq -r '.user.login // "unknown"')

if [[ "$STATE" == "" ]]; then
  echo "Error: Could not fetch PR. Check the URL and token." >&2
  exit 1
fi

# --- Fetch diff ---
DIFF=$(curl -s -H "$AUTH_HEADER" -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM")

# --- Fetch files ---
FILES_DATA=$(curl -s -H "$AUTH_HEADER" \
  "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUM/files")

# --- Analyze ---
RISKS=""
SUGGESTIONS=""
TOTAL_LINES=$((ADDED + DELETED))

# Confidence scoring
CONFIDENCE="Medium"
if [[ $TOTAL_LINES -lt 50 ]]; then
  CONFIDENCE="High"
elif [[ $TOTAL_LINES -gt 500 ]]; then
  CONFIDENCE="Low"
fi

# Risk detection
# 1. Large diff
if [[ $ADDED -gt 400 ]]; then
  RISKS="${RISKS}- Large PR (+${ADDED} lines) — hard to review thoroughly, consider splitting\n"
  CONFIDENCE="Low"
fi

# 2. Many files changed
if [[ $CHANGED_FILES -gt 20 ]]; then
  RISKS="${RISKS}- ${CHANGED_FILES} files changed — increases surface area for bugs\n"
fi

# 3. Delete-heavy changes
if [[ $DELETED -gt $ADDED ]] && [[ $DELETED -gt 100 ]]; then
  RISKS="${RISKS}- More deletions than additions (-${DELETED} vs +${ADDED}) — verify no accidental removals\n"
fi

# 4. Binary files
BINARIES=$(echo "$FILES_DATA" | jq -r '.[] | select(.status=="added") | .filename' | grep -E '\.(png|jpg|jpeg|gif|svg|ico|woff|ttf|eot|zip|tar|gz|bin|exe)$' || true)
if [[ -n "$BINARIES" ]]; then
  BIN_COUNT=$(echo "$BINARIES" | wc -l | tr -d ' ')
  RISKS="${RISKS}- ${BIN_COUNT} binary file(s) added — review file sizes and necessity\n"
fi

# 5. Config/environment files changed
CONFIG_FILES=$(echo "$FILES_DATA" | jq -r '.[] | .filename' | grep -iE '(\.env|secrets|credentials|password|private[_-]?key|config\.(yml|yaml|json|toml))' || true)
if [[ -n "$CONFIG_FILES" ]]; then
  RISKS="${RISKS}- Sensitive config files modified: $(echo "$CONFIG_FILES" | tr '\n' ', ') — check for leaked secrets\n"
  CONFIDENCE="Low"
fi

# 6. Database migration files
MIGRATION_FILES=$(echo "$FILES_DATA" | jq -r '.[] | .filename' | grep -iE '(migration|migrate)' || true)
if [[ -n "$MIGRATION_FILES" ]]; then
  RISKS="${RISKS}- Database migration files changed — verify reversibility and test on staging first\n"
fi

# Suggestion detection
# 1. No PR description
if [[ "$BODY" == "(no description)" || ${#BODY} -lt 50 ]]; then
  SUGGESTIONS="${SUGGESTIONS}- Add a PR description explaining the motivation and approach (currently minimal)\n"
fi

# 2. Test coverage
TEST_FILES=$(echo "$FILES_DATA" | jq -r '.[] | .filename' | grep -iE '(test|spec|__tests__)' || true)
if [[ -z "$TEST_FILES" && $ADDED -gt 30 ]]; then
  SUGGESTIONS="${SUGGESTIONS}- No test files in this PR — consider adding tests for new/changed logic\n"
fi

# 3. Breaking change signals
if echo "$BODY$TITLE" | grep -qiE '(breaking|breaking.change|bc|semver.major)'; then
  SUGGESTIONS="${SUGGESTIONS}- PR mentions breaking changes — ensure changelog entry and migration guide are included\n"
fi

# 4. TODO/FIXME in diff
TODOS=$(echo "$DIFF" | grep -iE '(TODO|FIXME|HACK|XXX)' | head -5 || true)
if [[ -n "$TODOS" ]]; then
  TODO_COUNT=$(echo "$TODOS" | wc -l | tr -d ' ')
  SUGGESTIONS="${SUGGESTIONS}- ${TODO_COUNT} TODO/FIXME/HACK comment(s) found in diff — resolve or create follow-up issues\n"
fi

# --- Build review ---
SUMMARY="This PR by @${AUTHOR} adds ${ADDED} and removes ${DELETED} lines across ${CHANGED_FILES} file(s)"
if [[ -n "$MIGRATION_FILES" ]]; then
  SUMMARY="${SUMMARY}, including database migrations"
fi
SUMMARY="${SUMMARY}. Merging into \`${BASE}\` from \`${HEAD}\`."

if [[ "$MERGEABLE" == "false" ]]; then
  RISKS="${RISKS}- PR has merge conflicts — rebase on latest \`${BASE}\` before review\n"
  CONFIDENCE="Low"
fi

# --- Output ---
REVIEW="## PR Review: ${TITLE}

**Author:** @${AUTHOR} | **${ADDED} additions** / **${DELETED} deletions** / **${CHANGED_FILES} files**

### Summary
${SUMMARY}

### Risks
${RISKS:-None identified.}

### Improvement Suggestions
${SUGGESTIONS:-None suggested.}

### Confidence: ${CONFIDENCE}

---
*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) — automated PR review tool*"

# --- Post or print ---
if [[ "$POST_COMMENT" == "true" ]]; then
  if [[ -z "$TOKEN" ]]; then
    echo "Error: GH_TOKEN or GITHUB_TOKEN required for posting comments." >&2
    exit 1
  fi
  RESPONSE=$(curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    "https://api.github.com/repos/$OWNER_REPO/issues/$PR_NUM/comments" \
    -d "$(jq -n --arg body "$REVIEW" '{body: $body}')")
  COMMENT_URL=$(echo "$RESPONSE" | jq -r '.html_url // .message')
  echo "Review posted: $COMMENT_URL"
else
  echo -e "$REVIEW"
fi