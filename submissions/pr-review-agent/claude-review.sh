#!/usr/bin/env bash
# claude-review.sh - CLI tool that reviews GitHub PRs and outputs structured Markdown
# Usage: bash claude-review.sh https://github.com/owner/repo/pull/123
# Dependencies: gh (GitHub CLI), authenticated via gh auth login

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: bash claude-review.sh <PR_URL>"
  echo "       bash claude-review.sh https://github.com/owner/repo/pull/123"
  echo ""
  echo "Options:"
  echo "  --output FILE   Write output to FILE instead of stdout"
  echo "  --help          Show this help message"
  exit 1
fi

OUTPUT_FILE=""
PR_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      echo "claude-review.sh - PR review agent with structured Markdown output"
      echo ""
      echo "Usage: bash claude-review.sh [OPTIONS] <PR_URL>"
      echo ""
      echo "Options:"
      echo "  --output FILE   Write review to FILE instead of stdout"
      echo "  --help          Show this help message"
      echo ""
      echo "Examples:"
      echo "  bash claude-review.sh https://github.com/facebook/react/pull/28000"
      echo "  bash claude-review.sh --output review.md https://github.com/owner/repo/pull/42"
      exit 0
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    *)
      PR_URL="$1"
      shift
      ;;
  esac
done

if [[ -z "$PR_URL" ]]; then
  echo "Error: PR URL is required." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Parse the PR URL into owner/repo and PR number
# ---------------------------------------------------------------------------

if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"
  FULL_REPO="${OWNER}/${REPO}"
else
  echo "Error: Could not parse PR URL. Expected: https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Verify gh CLI is available and authenticated
# ---------------------------------------------------------------------------

if ! command -v gh &>/dev/null; then
  echo "Error: GitHub CLI (gh) is not installed. Install from https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "Error: GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

echo "Reviewing PR #${PR_NUMBER} in ${FULL_REPO}..." >&2

# ---------------------------------------------------------------------------
# Fetch PR diff
# ---------------------------------------------------------------------------

PR_DIFF=$(gh pr diff "$PR_NUMBER" --repo "$FULL_REPO" 2>&1) || {
  echo "Error: Failed to fetch PR diff." >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Extract PR metadata using gh --jq (zero external dependencies)
# ---------------------------------------------------------------------------

GH_VIEW="gh pr view $PR_NUMBER --repo $FULL_REPO"

PR_TITLE=$($GH_VIEW --json title --jq '.title // ""' 2>/dev/null || echo "Unknown")
PR_AUTHOR=$($GH_VIEW --json author --jq '.author.login // "Unknown"' 2>/dev/null || echo "Unknown")
PR_STATE=$($GH_VIEW --json state --jq '.state // "Unknown"' 2>/dev/null || echo "Unknown")
PR_BASE=$($GH_VIEW --json baseRefName --jq '.baseRefName // ""' 2>/dev/null || echo "")
PR_HEAD=$($GH_VIEW --json headRefName --jq '.headRefName // ""' 2>/dev/null || echo "")
PR_BODY=$($GH_VIEW --json body --jq '.body // "No description." | .[:500]' 2>/dev/null || echo "No description.")
TOTAL_ADDITIONS=$($GH_VIEW --json additions --jq '.additions // 0' 2>/dev/null || echo "0")
TOTAL_DELETIONS=$($GH_VIEW --json deletions --jq '.deletions // 0' 2>/dev/null || echo "0")
CHANGED_FILES=$($GH_VIEW --json changedFiles --jq '.changedFiles // 0' 2>/dev/null || echo "0")

FILE_LIST=$($GH_VIEW --json files --jq '.files[] | "\(.path)|\(.additions)|\(.deletions)"' 2>/dev/null || echo "")

# ---------------------------------------------------------------------------
# Risk pattern detection on added lines in the diff
# ---------------------------------------------------------------------------

count_pattern() {
  local result
  result=$(echo "$PR_DIFF" | grep -cEi "$1" 2>/dev/null) || true
  echo "${result:-0}"
}

SECRET_HITS=$(count_pattern '^\+.*(api_key|apikey|secret|password|token|credential|private_key)\s*[:=]')
TODO_HITS=$(count_pattern '^\+.*(TODO|FIXME|HACK|XXX|WORKAROUND)')
DEBUG_HITS=$(count_pattern '^\+.*(console\.(log|debug|warn)|print\(|debugger|binding\.pry|pdb\.set_trace)')
ERROR_HANDLING_HITS=$(count_pattern '^\+.*(\.catch\(\s*\)|catch\s*\{\s*\}|except:\s*$|except\s+Exception\s*:)')
ENV_HITS=$(count_pattern '^\+.*(process\.env\.|os\.environ|ENV\[|getenv\()')
EVAL_HITS=$(count_pattern '^\+.*(eval\(|exec\(|Function\()')
SECURITY_DISABLE_HITS=$(count_pattern '^\+.*(disable.*ssl|verify\s*=\s*false|no.verify|insecure)')

TOTAL_RISK_HITS=$((SECRET_HITS + TODO_HITS + DEBUG_HITS + ERROR_HANDLING_HITS + EVAL_HITS + SECURITY_DISABLE_HITS))

# Large file detection
LARGE_FILE_HITS=0
if [[ -n "$FILE_LIST" ]]; then
  while IFS='|' read -r fpath fadds fdels; do
    if [[ "$fadds" -gt 500 ]] 2>/dev/null; then
      LARGE_FILE_HITS=$((LARGE_FILE_HITS + 1))
    fi
  done <<< "$FILE_LIST"
fi

# ---------------------------------------------------------------------------
# Good pattern detection
# ---------------------------------------------------------------------------

TEST_FILES=0
DOC_FILES=0
CONFIG_FILES=0
SRC_FILES=0

if [[ -n "$FILE_LIST" ]]; then
  TEST_FILES=$(echo "$FILE_LIST" | grep -ciE '(test|spec|__tests__)' 2>/dev/null) || true
  TEST_FILES=${TEST_FILES:-0}
  DOC_FILES=$(echo "$FILE_LIST" | grep -ciE '^[^|]*\.(md|rst|txt|doc)\|' 2>/dev/null) || true
  DOC_FILES=${DOC_FILES:-0}
  CONFIG_FILES=$(echo "$FILE_LIST" | grep -ciE '(\.yml|\.yaml|\.toml|\.json|Dockerfile|\.github/)' 2>/dev/null) || true
  CONFIG_FILES=${CONFIG_FILES:-0}
  SRC_FILES=$(echo "$FILE_LIST" | grep -ciE '\.(js|ts|jsx|tsx|py|rb|go|rs|java|c|cpp|cs|php|swift|kt)\|' 2>/dev/null) || true
  SRC_FILES=${SRC_FILES:-0}
fi

TYPE_HITS=$(count_pattern '^\+.*(: (string|number|boolean|int|float|str|List|Dict|Optional|Union)|interface |type )')

# ---------------------------------------------------------------------------
# PR size category
# ---------------------------------------------------------------------------

TOTAL_CHANGES=$((TOTAL_ADDITIONS + TOTAL_DELETIONS))

if [[ $TOTAL_CHANGES -lt 50 ]]; then SIZE_LABEL="XS (trivial)"
elif [[ $TOTAL_CHANGES -lt 200 ]]; then SIZE_LABEL="Small"
elif [[ $TOTAL_CHANGES -lt 500 ]]; then SIZE_LABEL="Medium"
elif [[ $TOTAL_CHANGES -lt 1000 ]]; then SIZE_LABEL="Large"
else SIZE_LABEL="XL (very large)"
fi

# ---------------------------------------------------------------------------
# Confidence score calculation
# ---------------------------------------------------------------------------

SCORE=100

# Size penalty
if [[ $TOTAL_CHANGES -gt 1000 ]]; then SCORE=$((SCORE - 25))
elif [[ $TOTAL_CHANGES -gt 500 ]]; then SCORE=$((SCORE - 15))
elif [[ $TOTAL_CHANGES -gt 200 ]]; then SCORE=$((SCORE - 5))
fi

# Risk penalties
SCORE=$((SCORE - SECRET_HITS * 15))
SCORE=$((SCORE - TODO_HITS * 3))
SCORE=$((SCORE - DEBUG_HITS * 5))
SCORE=$((SCORE - LARGE_FILE_HITS * 10))
SCORE=$((SCORE - ERROR_HANDLING_HITS * 8))
SCORE=$((SCORE - EVAL_HITS * 12))
SCORE=$((SCORE - SECURITY_DISABLE_HITS * 15))

# Good pattern bonuses
if [[ $TEST_FILES -gt 0 ]]; then SCORE=$((SCORE + 10)); fi
if [[ $DOC_FILES -gt 0 ]]; then SCORE=$((SCORE + 5)); fi
if [[ $TYPE_HITS -gt 0 ]]; then SCORE=$((SCORE + 5)); fi

# Clamp 0-100
if [[ $SCORE -lt 0 ]]; then SCORE=0; fi
if [[ $SCORE -gt 100 ]]; then SCORE=100; fi

if [[ $SCORE -ge 75 ]]; then CONFIDENCE="High"; CONFIDENCE_ICON="🟢"
elif [[ $SCORE -ge 40 ]]; then CONFIDENCE="Medium"; CONFIDENCE_ICON="🟡"
else CONFIDENCE="Low"; CONFIDENCE_ICON="🔴"
fi

# ---------------------------------------------------------------------------
# Build summary text
# ---------------------------------------------------------------------------

CHANGE_TYPE="modifies"
if [[ $TOTAL_ADDITIONS -gt $((TOTAL_DELETIONS * 3 + 1)) ]]; then CHANGE_TYPE="adds"
elif [[ $TOTAL_DELETIONS -gt $((TOTAL_ADDITIONS * 3 + 1)) ]]; then CHANGE_TYPE="removes"
elif [[ $TOTAL_ADDITIONS -gt $TOTAL_DELETIONS ]]; then CHANGE_TYPE="primarily adds"
else CHANGE_TYPE="refactors"
fi

SUMMARY_LINE1="This PR ${CHANGE_TYPE} code across ${CHANGED_FILES} file(s) with +${TOTAL_ADDITIONS}/-${TOTAL_DELETIONS} line changes (${SIZE_LABEL})."

SUMMARY_PARTS=""
if [[ $TEST_FILES -gt 0 ]]; then SUMMARY_PARTS="${SUMMARY_PARTS} Includes ${TEST_FILES} test file(s)."; fi
if [[ $DOC_FILES -gt 0 ]]; then SUMMARY_PARTS="${SUMMARY_PARTS} Updates ${DOC_FILES} documentation file(s)."; fi
if [[ $CONFIG_FILES -gt 0 ]]; then SUMMARY_PARTS="${SUMMARY_PARTS} Touches ${CONFIG_FILES} config/CI file(s)."; fi
if [[ -z "$SUMMARY_PARTS" ]]; then SUMMARY_PARTS=" No test or documentation changes detected."; fi

# ---------------------------------------------------------------------------
# Build risk list
# ---------------------------------------------------------------------------

RISKS=""
add_risk() { RISKS="${RISKS}
- $1"; }

if [[ $SECRET_HITS -gt 0 ]]; then add_risk "**Possible hardcoded secrets/credentials** detected (${SECRET_HITS} occurrence(s)). Verify no API keys or passwords are committed."; fi
if [[ $TODO_HITS -gt 0 ]]; then add_risk "**TODO/FIXME/HACK markers** found (${TODO_HITS} occurrence(s)). These may indicate incomplete implementation."; fi
if [[ $DEBUG_HITS -gt 0 ]]; then add_risk "**Debug statements** detected (${DEBUG_HITS} occurrence(s)). Should be removed before merge."; fi
if [[ $LARGE_FILE_HITS -gt 0 ]]; then add_risk "**Large file changes** (${LARGE_FILE_HITS} file(s) with >500 added lines). Consider splitting into smaller PRs."; fi
if [[ $ERROR_HANDLING_HITS -gt 0 ]]; then add_risk "**Empty/weak error handling** found (${ERROR_HANDLING_HITS} occurrence(s)). Errors may be silently swallowed."; fi
if [[ $EVAL_HITS -gt 0 ]]; then add_risk "**Dynamic code execution** (eval/exec) detected (${EVAL_HITS} occurrence(s)). Potential code injection vector."; fi
if [[ $SECURITY_DISABLE_HITS -gt 0 ]]; then add_risk "**Security features disabled** (${SECURITY_DISABLE_HITS} occurrence(s)). SSL/security checks may be bypassed."; fi
if [[ $ENV_HITS -gt 0 ]]; then add_risk "**Environment variable access** detected (${ENV_HITS} occurrence(s)). Ensure defaults/fallbacks are provided."; fi
if [[ $TOTAL_CHANGES -gt 500 ]]; then add_risk "**PR size** is ${SIZE_LABEL} (${TOTAL_CHANGES} total changes). Large PRs are harder to review thoroughly."; fi
if [[ -z "$RISKS" ]]; then RISKS="
- No significant risks detected."; fi

# ---------------------------------------------------------------------------
# Build suggestion list
# ---------------------------------------------------------------------------

SUGGESTIONS=""
add_suggestion() { SUGGESTIONS="${SUGGESTIONS}
- $1"; }

if [[ $TEST_FILES -eq 0 && $SRC_FILES -gt 0 ]]; then add_suggestion "**Add tests**: No test files detected. Consider adding unit or integration tests."; fi
if [[ $DOC_FILES -eq 0 && $TOTAL_ADDITIONS -gt 100 ]]; then add_suggestion "**Update documentation**: Significant code additions without documentation updates."; fi
if [[ $TYPE_HITS -eq 0 && $SRC_FILES -gt 0 ]]; then add_suggestion "**Add type annotations**: No type hints detected. Types improve maintainability."; fi
if [[ $TOTAL_CHANGES -gt 500 ]]; then add_suggestion "**Consider splitting**: This PR is large. Smaller PRs are easier to review."; fi
if [[ $DEBUG_HITS -gt 0 ]]; then add_suggestion "**Clean up debug statements**: Remove console.log/print/debugger calls before merging."; fi
if [[ $TODO_HITS -gt 0 ]]; then add_suggestion "**Resolve TODOs**: Address or file issues for TODO/FIXME items before merging."; fi
if [[ -z "$SUGGESTIONS" ]]; then SUGGESTIONS="
- PR looks well-structured. No additional suggestions."; fi

# ---------------------------------------------------------------------------
# Build file change table
# ---------------------------------------------------------------------------

FILE_TABLE="| File | Additions | Deletions |
|------|-----------|-----------|"
if [[ -n "$FILE_LIST" ]]; then
  while IFS='|' read -r fpath fadds fdels; do
    FILE_TABLE="${FILE_TABLE}
| \`${fpath}\` | +${fadds} | -${fdels} |"
  done <<< "$FILE_LIST"
fi

# ---------------------------------------------------------------------------
# Scoring breakdown details
# ---------------------------------------------------------------------------

SIZE_NOTE="Small PR: no penalty"
if [[ $TOTAL_CHANGES -gt 1000 ]]; then SIZE_NOTE="XL PR: -25"
elif [[ $TOTAL_CHANGES -gt 500 ]]; then SIZE_NOTE="Large PR: -15"
elif [[ $TOTAL_CHANGES -gt 200 ]]; then SIZE_NOTE="Medium PR: -5"
fi

RISK_BREAKDOWN=""
if [[ $SECRET_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- Secrets: -$((SECRET_HITS * 15))"; fi
if [[ $TODO_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- TODOs: -$((TODO_HITS * 3))"; fi
if [[ $DEBUG_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- Debug stmts: -$((DEBUG_HITS * 5))"; fi
if [[ $LARGE_FILE_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- Large files: -$((LARGE_FILE_HITS * 10))"; fi
if [[ $ERROR_HANDLING_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- Error handling: -$((ERROR_HANDLING_HITS * 8))"; fi
if [[ $EVAL_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- eval/exec: -$((EVAL_HITS * 12))"; fi
if [[ $SECURITY_DISABLE_HITS -gt 0 ]]; then RISK_BREAKDOWN="${RISK_BREAKDOWN}
- Security disabled: -$((SECURITY_DISABLE_HITS * 15))"; fi
if [[ -z "$RISK_BREAKDOWN" ]]; then RISK_BREAKDOWN="
- None detected"; fi

GOOD_BREAKDOWN=""
if [[ $TEST_FILES -gt 0 ]]; then GOOD_BREAKDOWN="${GOOD_BREAKDOWN}
- Tests included: +10"; fi
if [[ $DOC_FILES -gt 0 ]]; then GOOD_BREAKDOWN="${GOOD_BREAKDOWN}
- Docs updated: +5"; fi
if [[ $TYPE_HITS -gt 0 ]]; then GOOD_BREAKDOWN="${GOOD_BREAKDOWN}
- Types added: +5"; fi
if [[ -z "$GOOD_BREAKDOWN" ]]; then GOOD_BREAKDOWN="
- None detected"; fi

# ---------------------------------------------------------------------------
# Generate final Markdown output
# ---------------------------------------------------------------------------

DATESTAMP=$(date -u '+%Y-%m-%d %H:%M UTC')

REVIEW="# PR Review: ${PR_TITLE}

> **PR**: [#${PR_NUMBER}](${PR_URL}) in \`${FULL_REPO}\`
> **Author**: @${PR_AUTHOR} | **State**: ${PR_STATE}
> **Branch**: \`${PR_HEAD}\` -> \`${PR_BASE}\`
> **Generated**: ${DATESTAMP}

---

## Summary

${SUMMARY_LINE1}${SUMMARY_PARTS}

## Stats

| Metric | Value |
|--------|-------|
| Files changed | ${CHANGED_FILES} |
| Lines added | +${TOTAL_ADDITIONS} |
| Lines removed | -${TOTAL_DELETIONS} |
| Total changes | ${TOTAL_CHANGES} |
| PR size | ${SIZE_LABEL} |

## Files Changed

${FILE_TABLE}

## Identified Risks
${RISKS}

## Improvement Suggestions
${SUGGESTIONS}

## Confidence Score

| Score | Level |
|-------|-------|
| ${SCORE}/100 | ${CONFIDENCE_ICON} **${CONFIDENCE}** |

<details>
<summary>Scoring Breakdown</summary>

**Base score**: 100

**Size adjustments**:
- ${SIZE_NOTE}

**Risk penalties**:${RISK_BREAKDOWN}

**Good pattern bonuses**:${GOOD_BREAKDOWN}

**Final**: ${SCORE}/100 -> **${CONFIDENCE}**

</details>

---

*Generated by [claude-review.sh](https://github.com/claude-builders-bounty/claude-builders-bounty) -- a CLI PR review agent using pattern-based analysis. No API keys required.*"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REVIEW" > "$OUTPUT_FILE"
  echo "Review written to ${OUTPUT_FILE}" >&2
else
  echo "$REVIEW"
fi

echo "" >&2
echo "Review complete: ${CONFIDENCE_ICON} ${CONFIDENCE} confidence (${SCORE}/100)" >&2
