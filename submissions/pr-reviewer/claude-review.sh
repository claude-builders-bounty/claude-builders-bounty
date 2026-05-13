#!/usr/bin/env bash
set -euo pipefail

# claude-review: Review a GitHub PR and output structured Markdown feedback
# Usage: bash claude-review.sh --pr https://github.com/owner/repo/pull/123

PR_URL=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR_URL="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash claude-review.sh --pr <github-pr-url> [--output <file>]"
      echo "  --pr      GitHub PR URL (required)"
      echo "  --output  Save review to file (default: stdout)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: --pr <url> is required"
  echo "Usage: bash claude-review.sh --pr https://github.com/owner/repo/pull/123"
  exit 1
fi

if ! command -v gh &> /dev/null; then
  echo "Error: GitHub CLI (gh) is required. Install: https://cli.github.com"
  exit 1
fi

# Extract owner/repo and PR number from URL
PR_PATH=$(echo "$PR_URL" | sed -E 's|https?://github\.com/||' | sed 's|/$||')
OWNER_REPO=$(echo "$PR_PATH" | cut -d'/' -f1,2)
PR_NUMBER=$(echo "$PR_PATH" | grep -oE '[0-9]+$')

if [[ -z "$OWNER_REPO" || -z "$PR_NUMBER" ]]; then
  echo "Error: could not parse PR URL. Expected format: https://github.com/owner/repo/pull/123"
  exit 1
fi

echo "Reviewing PR #${PR_NUMBER} in ${OWNER_REPO}..." >&2

# Fetch PR metadata
PR_TITLE=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json title --jq '.title' 2>/dev/null || echo "Unknown")
PR_BODY=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json body --jq '.body' 2>/dev/null || echo "")
PR_AUTHOR=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json author --jq '.author.login' 2>/dev/null || echo "Unknown")
FILES_CHANGED=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json files --jq '.files | length' 2>/dev/null || echo "?")
ADDITIONS=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json additions --jq '.additions' 2>/dev/null || echo "?")
DELETIONS=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json deletions --jq '.deletions' 2>/dev/null || echo "?")

# Fetch the diff
DIFF=$(gh pr diff "$PR_NUMBER" --repo "$OWNER_REPO" 2>/dev/null || echo "Error fetching diff")

# Truncate very large diffs to avoid overwhelming analysis
DIFF_LINES=$(echo "$DIFF" | wc -l | tr -d ' ')
if [[ "$DIFF_LINES" -gt 500 ]]; then
  DIFF=$(echo "$DIFF" | head -500)
  DIFF_TRUNCATED="true"
else
  DIFF_TRUNCATED="false"
fi

# Fetch changed file names
FILE_LIST=$(gh pr view "$PR_NUMBER" --repo "$OWNER_REPO" --json files --jq '.files[].path' 2>/dev/null || echo "")

# Analyze the diff
analyze_diff() {
  local diff="$1"
  local risks=""
  local suggestions=""
  local summary_points=""
  local confidence="Medium"

  # Check for common risk patterns
  if echo "$diff" | grep -qiE '(password|secret|api.key|token|credential)'; then
    risks="${risks}\n- **Potential credential exposure**: Code references passwords, secrets, or API keys. Verify no sensitive values are hardcoded."
  fi

  if echo "$diff" | grep -qiE '(TODO|FIXME|HACK|XXX)'; then
    risks="${risks}\n- **Unfinished work markers**: Contains TODO/FIXME/HACK comments that may indicate incomplete implementation."
  fi

  if echo "$diff" | grep -qiE 'console\.(log|debug|warn)'; then
    suggestions="${suggestions}\n- Consider removing \`console.log\`/\`console.debug\` statements before merging to production."
  fi

  if echo "$diff" | grep -qiE '(eval\(|exec\(|subprocess|child_process|dangerouslySetInnerHTML)'; then
    risks="${risks}\n- **Security concern**: Uses potentially dangerous functions (eval/exec/dangerouslySetInnerHTML). Ensure input is sanitized."
  fi

  if echo "$diff" | grep -qiE 'catch\s*\(\s*\)|\bcatch\b.*\{\s*\}'; then
    suggestions="${suggestions}\n- Empty catch blocks swallow errors silently. Consider logging or re-throwing."
  fi

  if [[ "$ADDITIONS" -gt 300 ]]; then
    suggestions="${suggestions}\n- Large PR (${ADDITIONS}+ lines added). Consider splitting into smaller, focused PRs for easier review."
    confidence="Low"
  fi

  if echo "$diff" | grep -qE '^\+.*\bany\b' && echo "$FILE_LIST" | grep -qE '\.tsx?$'; then
    suggestions="${suggestions}\n- TypeScript \`any\` type detected. Consider using specific types for better type safety."
  fi

  if echo "$diff" | grep -qiE '(\.env|credentials|\.pem|\.key)' && echo "$diff" | grep -qE '^\+'; then
    risks="${risks}\n- **Sensitive file reference**: Changes reference environment/credential files. Ensure \`.gitignore\` is properly configured."
  fi

  # Determine confidence based on diff size and complexity
  if [[ "$DIFF_LINES" -lt 50 ]]; then
    confidence="High"
  elif [[ "$DIFF_LINES" -lt 200 ]]; then
    confidence="Medium"
  fi

  # Default messages if no specific issues found
  if [[ -z "$risks" ]]; then
    risks="\n- No significant risks identified in automated analysis."
  fi
  if [[ -z "$suggestions" ]]; then
    suggestions="\n- No specific suggestions from automated analysis. Manual review recommended."
  fi

  # Categorize changes
  local has_tests="false"
  local has_docs="false"
  local has_config="false"
  if echo "$FILE_LIST" | grep -qiE '(test|spec|__tests__)'; then has_tests="true"; fi
  if echo "$FILE_LIST" | grep -qiE '(README|CHANGELOG|docs/|\.md$)'; then has_docs="true"; fi
  if echo "$FILE_LIST" | grep -qiE '(package\.json|tsconfig|eslint|\.config\.)'; then has_config="true"; fi

  # Build summary
  summary_points="This PR modifies **${FILES_CHANGED} files** (+${ADDITIONS}/-${DELETIONS} lines)"
  if [[ "$has_tests" == "true" ]]; then summary_points="${summary_points}, including test changes"; fi
  if [[ "$has_docs" == "true" ]]; then summary_points="${summary_points}, with documentation updates"; fi
  if [[ "$has_config" == "true" ]]; then summary_points="${summary_points}, with configuration changes"; fi

  # Output the review
  cat << REVIEW
# PR Review: ${PR_TITLE}

**PR:** [#${PR_NUMBER}](${PR_URL}) by @${PR_AUTHOR}
**Scope:** ${FILES_CHANGED} files changed (+${ADDITIONS}/-${DELETIONS})
**Confidence:** ${confidence}

---

## Summary

${summary_points}.

## Changed Files

$(echo "$FILE_LIST" | sed 's/^/- `/' | sed 's/$/`/')

## Identified Risks
$(echo -e "$risks")

## Improvement Suggestions
$(echo -e "$suggestions")

## Checklist

- [$([ "$has_tests" = "true" ] && echo "x" || echo " ")] Tests included or updated
- [$([ "$has_docs" = "true" ] && echo "x" || echo " ")] Documentation updated
- [ ] No sensitive data exposed
- [ ] Error handling adequate
$([ "$DIFF_TRUNCATED" = "true" ] && echo "
> **Note:** Diff was truncated (${DIFF_LINES} lines). Only the first 500 lines were analyzed." || echo "")

---
*Generated by claude-review*
REVIEW
}

REVIEW=$(analyze_diff "$DIFF")

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REVIEW" > "$OUTPUT_FILE"
  echo "Review saved to ${OUTPUT_FILE}" >&2
else
  echo "$REVIEW"
fi
