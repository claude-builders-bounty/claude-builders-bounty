#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# claude-review.sh — PR reviewer with structured Markdown output
#
# Fetches PR data via `gh` CLI, analyzes the diff for common patterns
# (security issues, debug statements, missing tests, large files), and
# produces a structured review with Summary, Risks, Suggestions, and
# Confidence level.
#
# Usage:
#   ./claude-review.sh --pr https://github.com/owner/repo/pull/123
#   ./claude-review.sh --pr owner/repo#123
#   ./claude-review.sh --pr 123                  (uses current repo)
#
# Options:
#   --pr <url|ref>     PR URL or number (required)
#   --output <file>    Write review to file (default: stdout)
#   --help             Show this help
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
PR_REF=""
OUTPUT=""

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr)     PR_REF="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --help)
            sed -n '3,17p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$PR_REF" ]]; then
    echo "Error: --pr is required" >&2
    echo "Usage: ./claude-review.sh --pr <url|number>" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Check dependencies
# ---------------------------------------------------------------------------
check_deps() {
    if ! command -v gh &>/dev/null; then
        echo "Error: gh CLI is required. Install: https://cli.github.com/" >&2
        exit 1
    fi

    if ! gh auth status &>/dev/null 2>&1; then
        echo "Error: gh is not authenticated. Run: gh auth login" >&2
        exit 1
    fi
}

check_deps

# ---------------------------------------------------------------------------
# Parse PR reference into owner/repo and number
# ---------------------------------------------------------------------------
parse_pr_ref() {
    local ref="$1"
    local repo=""
    local number=""

    # Full URL: https://github.com/owner/repo/pull/123
    if [[ "$ref" =~ github\.com/([^/]+/[^/]+)/pull/([0-9]+) ]]; then
        repo="${BASH_REMATCH[1]}"
        number="${BASH_REMATCH[2]}"
    # owner/repo#123
    elif [[ "$ref" =~ ^([^/]+/[^#]+)#([0-9]+)$ ]]; then
        repo="${BASH_REMATCH[1]}"
        number="${BASH_REMATCH[2]}"
    # Just a number (use current repo)
    elif [[ "$ref" =~ ^[0-9]+$ ]]; then
        repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
        number="$ref"
        if [[ -z "$repo" ]]; then
            echo "Error: could not detect repo. Use full URL or owner/repo#number format." >&2
            exit 1
        fi
    else
        echo "Error: unrecognized PR reference format: $ref" >&2
        exit 1
    fi

    echo "${repo}|${number}"
}

PARSED="$(parse_pr_ref "$PR_REF")"
REPO="${PARSED%%|*}"
PR_NUMBER="${PARSED##*|}"

# ---------------------------------------------------------------------------
# Fetch PR data
# ---------------------------------------------------------------------------
echo "Fetching PR #${PR_NUMBER} from ${REPO}..." >&2

PR_JSON="$(gh api "repos/${REPO}/pulls/${PR_NUMBER}" 2>/dev/null || true)"

if [[ -z "$PR_JSON" ]]; then
    echo "Error: could not fetch PR #${PR_NUMBER} from ${REPO}" >&2
    exit 1
fi

# Extract fields with jq or fallback
extract_field() {
    local json="$1"
    local field="$2"

    if command -v jq &>/dev/null; then
        echo "$json" | jq -r "$field // empty" 2>/dev/null || true
    else
        echo "$json" | grep -oP "\"${field}\"\s*:\s*\"((?:[^\"\\\\]|\\\\.)*)\"" | head -1 | sed 's/.*: *"//;s/"$//' || true
    fi
}

PR_TITLE="$(extract_field "$PR_JSON" '.title')"
PR_AUTHOR="$(extract_field "$PR_JSON" '.user.login')"
PR_BASE="$(extract_field "$PR_JSON" '.base.ref')"
PR_HEAD="$(extract_field "$PR_JSON" '.head.ref')"
PR_BODY="$(extract_field "$PR_JSON" '.body')"

if command -v jq &>/dev/null; then
    PR_ADDITIONS="$(echo "$PR_JSON" | jq -r '.additions // 0')"
    PR_DELETIONS="$(echo "$PR_JSON" | jq -r '.deletions // 0')"
    PR_CHANGED_FILES="$(echo "$PR_JSON" | jq -r '.changed_files // 0')"
else
    PR_ADDITIONS="$(echo "$PR_JSON" | grep -oP '"additions"\s*:\s*\K[0-9]+' | head -1 || echo "0")"
    PR_DELETIONS="$(echo "$PR_JSON" | grep -oP '"deletions"\s*:\s*\K[0-9]+' | head -1 || echo "0")"
    PR_CHANGED_FILES="$(echo "$PR_JSON" | grep -oP '"changed_files"\s*:\s*\K[0-9]+' | head -1 || echo "0")"
fi

# Fetch the diff
DIFF="$(gh api "repos/${REPO}/pulls/${PR_NUMBER}" -H "Accept: application/vnd.github.v3.diff" 2>/dev/null || true)"

# Fetch changed file names
FILES_JSON="$(gh api "repos/${REPO}/pulls/${PR_NUMBER}/files?per_page=100" 2>/dev/null || true)"
if command -v jq &>/dev/null; then
    FILE_NAMES="$(echo "$FILES_JSON" | jq -r '.[].filename' 2>/dev/null || true)"
else
    FILE_NAMES="$(echo "$FILES_JSON" | grep -oP '"filename"\s*:\s*"\K[^"]+' || true)"
fi

echo "Analyzing ${PR_CHANGED_FILES} changed files (+${PR_ADDITIONS} -${PR_DELETIONS})..." >&2

# ---------------------------------------------------------------------------
# Analysis: scan diff for patterns
# ---------------------------------------------------------------------------
RISKS=()
SUGGESTIONS=()
STATS_ISSUES=0

# Security patterns
check_pattern() {
    local pattern="$1"
    local risk_msg="$2"
    local suggestion_msg="$3"

    if echo "$DIFF" | grep -qPi "$pattern" 2>/dev/null; then
        RISKS+=("$risk_msg")
        SUGGESTIONS+=("$suggestion_msg")
        STATS_ISSUES=$((STATS_ISSUES + 1))
    fi
}

# --- Security ---
check_pattern \
    '^\+.*\b(password|secret|api_key|apikey|token|private_key)\s*=\s*["\x27][^"\x27]+["\x27]' \
    "**Hardcoded secret detected** -- a password, API key, or token appears to be hardcoded in the diff" \
    "Move secrets to environment variables and load from .env files"

# Note: we detect dynamic code execution patterns that run arbitrary strings
check_pattern \
    '^\+.*\beval\s*\(' \
    "**Dynamic code execution** -- running arbitrary code strings is a common injection vector" \
    "Replace with safer alternatives (JSON.parse for data, explicit logic instead of dynamic execution)"

check_pattern \
    '^\+.*innerHTML\s*=' \
    "**innerHTML assignment** -- setting innerHTML with unsanitized input can lead to XSS" \
    "Use textContent for plain text, or sanitize input before using innerHTML"

check_pattern \
    '^\+.*\$_GET\[|^\+.*\$_POST\[|^\+.*\$_REQUEST\[' \
    "**Raw PHP superglobal access** -- using \$_GET/\$_POST/\$_REQUEST without validation" \
    "Use filter_input() or validate/sanitize before using request data"

check_pattern \
    '^\+.*query\s*\(.*\$' \
    "**Possible SQL injection** -- variable interpolation in a query string" \
    "Use prepared statements with parameterized queries"

# --- Debug statements ---
check_pattern \
    '^\+.*console\.(log|debug|warn|error)\(' \
    "**Console statements in production code** -- debug output left in the diff" \
    "Remove console.log/debug statements before merging"

check_pattern \
    '^\+.*(var_dump|print_r|error_log|dd)\(' \
    "**PHP debug output** -- var_dump/print_r/dd left in the diff" \
    "Remove debug output functions before merging"

# --- Code quality ---
check_pattern \
    '^\+.*TODO|^\+.*FIXME|^\+.*HACK|^\+.*XXX' \
    "**TODO/FIXME/HACK markers found** -- unfinished work flagged in the code" \
    "Address TODOs before merging, or create issues to track them"

check_pattern \
    '^\+.*catch\s*\([^)]*\)\s*\{\s*\}' \
    "**Empty catch block** -- errors are being silently swallowed" \
    "Log the error or handle it explicitly -- empty catch blocks hide bugs"

# --- Test coverage ---
HAS_TEST_FILES=false
if echo "$FILE_NAMES" | grep -qiP '\.(test|spec)\.(js|ts|jsx|tsx|py|php)$'; then
    HAS_TEST_FILES=true
fi

HAS_SRC_CHANGES=false
if echo "$FILE_NAMES" | grep -qiP '\.(js|ts|jsx|tsx|py|php)$' | grep -qvP '\.(test|spec)\.' 2>/dev/null; then
    HAS_SRC_CHANGES=true
fi

# Simple heuristic: if source files changed but no test files, flag it
if [[ "$HAS_SRC_CHANGES" == "true" ]] && [[ "$HAS_TEST_FILES" == "false" ]]; then
    if [[ $PR_ADDITIONS -gt 50 ]]; then
        RISKS+=("**No test files changed** -- ${PR_ADDITIONS}+ lines added with no corresponding test updates")
        SUGGESTIONS+=("Add tests covering the new functionality before merging")
        STATS_ISSUES=$((STATS_ISSUES + 1))
    fi
fi

# --- Large PR ---
if [[ $PR_ADDITIONS -gt 500 ]]; then
    RISKS+=("**Large PR** -- ${PR_ADDITIONS} additions across ${PR_CHANGED_FILES} files makes thorough review difficult")
    SUGGESTIONS+=("Consider splitting into smaller, focused PRs for easier review")
    STATS_ISSUES=$((STATS_ISSUES + 1))
fi

# ---------------------------------------------------------------------------
# Determine confidence level
# ---------------------------------------------------------------------------
determine_confidence() {
    local issues=$1
    local additions=$2

    if [[ $issues -ge 3 ]] || [[ $additions -gt 1000 ]]; then
        echo "Low"
    elif [[ $issues -ge 1 ]] || [[ $additions -gt 300 ]]; then
        echo "Medium"
    else
        echo "High"
    fi
}

CONFIDENCE="$(determine_confidence "$STATS_ISSUES" "$PR_ADDITIONS")"

# ---------------------------------------------------------------------------
# Generate summary
# ---------------------------------------------------------------------------
generate_summary() {
    local title="$1"
    local additions="$2"
    local deletions="$3"
    local files="$4"
    local base="$5"

    local change_type="modifies"
    if [[ $additions -gt $deletions ]] && [[ $deletions -lt 10 ]]; then
        change_type="adds"
    elif [[ $deletions -gt $additions ]] && [[ $additions -lt 10 ]]; then
        change_type="removes"
    elif [[ $additions -gt 0 ]] && [[ $deletions -gt 0 ]]; then
        change_type="refactors"
    fi

    echo "This PR ${change_type} code across ${files} file(s) (+${additions}/-${deletions}) targeting \`${base}\`. ${title}."

    if [[ ${#RISKS[@]} -gt 0 ]]; then
        echo "The diff contains ${#RISKS[@]} issue(s) that should be addressed before merging."
    else
        echo "No automated issues detected in the diff."
    fi
}

SUMMARY="$(generate_summary "$PR_TITLE" "$PR_ADDITIONS" "$PR_DELETIONS" "$PR_CHANGED_FILES" "$PR_BASE")"

# ---------------------------------------------------------------------------
# Build output
# ---------------------------------------------------------------------------
REVIEW=""

REVIEW+="# PR Review: #${PR_NUMBER}"$'\n\n'
REVIEW+="**${PR_TITLE}**"$'\n'
REVIEW+="Author: @${PR_AUTHOR} | Branch: \`${PR_HEAD}\` -> \`${PR_BASE}\` | Files: ${PR_CHANGED_FILES} | +${PR_ADDITIONS} / -${PR_DELETIONS}"$'\n\n'

REVIEW+="---"$'\n\n'

REVIEW+="## Summary"$'\n\n'
REVIEW+="${SUMMARY}"$'\n\n'

REVIEW+="## Risks"$'\n\n'
if [[ ${#RISKS[@]} -gt 0 ]]; then
    for risk in "${RISKS[@]}"; do
        REVIEW+="- ${risk}"$'\n'
    done
else
    REVIEW+="- No risks detected by automated analysis"$'\n'
fi
REVIEW+=$'\n'

REVIEW+="## Suggestions"$'\n\n'
if [[ ${#SUGGESTIONS[@]} -gt 0 ]]; then
    for suggestion in "${SUGGESTIONS[@]}"; do
        REVIEW+="- ${suggestion}"$'\n'
    done
else
    REVIEW+="- No suggestions -- this looks clean"$'\n'
fi
REVIEW+=$'\n'

REVIEW+="## Confidence"$'\n\n'
REVIEW+="**${CONFIDENCE}**"$'\n\n'

case "$CONFIDENCE" in
    High)   REVIEW+="Automated analysis found no issues. Manual review is still recommended for logic correctness."$'\n' ;;
    Medium) REVIEW+="Some potential issues detected. Review the flagged items before merging."$'\n' ;;
    Low)    REVIEW+="Multiple issues or a very large diff. Careful manual review is strongly recommended."$'\n' ;;
esac

REVIEW+=$'\n'
REVIEW+="---"$'\n'
REVIEW+="*Generated by claude-review.sh -- automated pattern analysis, not a substitute for human review.*"$'\n'

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if [[ -n "$OUTPUT" ]]; then
    echo "$REVIEW" > "$OUTPUT"
    echo "Review written to ${OUTPUT}" >&2
else
    echo "$REVIEW"
fi
