#!/usr/bin/env bash
# =============================================================================
# claude-review — AI-powered GitHub PR reviewer using Claude Code
# =============================================================================
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
#        claude-review --pr owner/repo#123
#        claude-review --help
#
# Requirements: gh (GitHub CLI) or curl + GITHUB_TOKEN, claude CLI
# =============================================================================
set -euo pipefail

# --- Configuration -----------------------------------------------------------
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
PR_URL=""
TIMEOUT="${TIMEOUT:-120}"
MODEL="${CLAUDE_MODEL:-claude-sonnet-4-20250514}"
TEMP_DIR=""

# --- Help --------------------------------------------------------------------
usage() {
    cat << 'EOF'
claude-review — AI-powered PR reviewer using Claude Code

USAGE:
    claude-review --pr URL

    URL formats:
      https://github.com/owner/repo/pull/123
      owner/repo#123

OPTIONS:
    --pr URL         GitHub PR to review (required)
    --timeout SEC    Timeout in seconds (default: 120)
    --model MODEL    Claude model to use (default: claude-sonnet-4-20250514)
    --help, -h       Show this help

ENVIRONMENT:
    GITHUB_TOKEN     GitHub personal access token (required if gh is unavailable)
    CLAUDE_BIN       Path to claude CLI (default: claude)
    CLAUDE_MODEL     Claude model to use

OUTPUT:
    Structured Markdown review with:
      - Summary (2-3 sentences)
      - Identified Risks (list)
      - Improvement Suggestions (list)
      - Confidence Score (Low/Medium/High)
EOF
    exit 0
}

# --- Cleanup -----------------------------------------------------------------
cleanup() {
    if [[ -n "${TEMP_DIR:-}" ]] && [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# --- Parse arguments ---------------------------------------------------------
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pr)
                shift
                PR_URL="${1:-}"
                ;;
            --timeout)
                shift
                TIMEOUT="${1:-$TIMEOUT}"
                ;;
            --model)
                shift
                MODEL="${1:-$MODEL}"
                ;;
            --help|-h)
                usage
                ;;
            *)
                echo "ERROR: Unknown argument: $1"
                usage
                ;;
        esac
        shift
    done

    if [[ -z "$PR_URL" ]]; then
        echo "ERROR: --pr is required. Use --help for usage."
        exit 1
    fi
}

# --- Parse PR URL into owner/repo/number -------------------------------------
parse_pr_url() {
    local url="$1"

    # Format: https://github.com/owner/repo/pull/123
    if [[ "$url" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        PR_NUMBER="${BASH_REMATCH[3]}"
        return 0
    fi

    # Format: owner/repo#123
    if [[ "$url" =~ ^([^/]+)/([^#]+)#([0-9]+)$ ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        PR_NUMBER="${BASH_REMATCH[3]}"
        return 0
    fi

    echo "ERROR: Unable to parse PR URL: $url"
    echo "       Expected formats: https://github.com/owner/repo/pull/123 or owner/repo#123"
    exit 1
}

# --- Check dependencies ------------------------------------------------------
check_deps() {
    local gh_available=false
    local curl_available=false
    local claude_available=false

    if command -v gh &>/dev/null; then
        gh_available=true
    fi

    if command -v curl &>/dev/null; then
        curl_available=true
    fi

    if command -v "$CLAUDE_BIN" &>/dev/null; then
        claude_available=true
    fi

    if ! $gh_available && ! $curl_available; then
        echo "ERROR: Neither 'gh' (GitHub CLI) nor 'curl' found."
        echo "       Install one: https://cli.github.com/ or use your system package manager."
        exit 1
    fi

    if ! $claude_available; then
        echo "WARNING: '$CLAUDE_BIN' not found in PATH."
        echo "         Install Claude Code: npm install -g @anthropic-ai/claude-code"
        echo "         Will run in simulated mode."
        echo ""
        CLAUDE_AVAILABLE=false
    else
        CLAUDE_AVAILABLE=true
    fi

    # If using curl, require GITHUB_TOKEN
    if ! $gh_available && [[ -z "$GITHUB_TOKEN" ]]; then
        echo "ERROR: GITHUB_TOKEN environment variable not set."
        echo "       gh CLI not found; set GITHUB_TOKEN for curl-based API access."
        echo "       Generate a token: https://github.com/settings/tokens"
        exit 1
    fi

    echo "Dependencies OK: gh=$( $gh_available && echo yes || echo no ), curl=$( $curl_available && echo yes || echo no ), claude=$( $claude_available && echo yes )"
}

# --- Fetch PR metadata (title, description, changed files) -------------------
fetch_pr_metadata() {
    local owner="$1" repo="$2" pr="$3"

    if command -v gh &>/dev/null; then
        echo "Fetching PR metadata via gh CLI..." >&2
        gh pr view "$pr" --repo "$owner/$repo" \
            --json title,body,additions,deletions,changedFiles,files,state,author \
            2>/dev/null
    else
        echo "Fetching PR metadata via GitHub API..." >&2
        curl -sf -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/$owner/$repo/pulls/$pr" 2>/dev/null
    fi
}

# --- Fetch PR diff -----------------------------------------------------------
fetch_pr_diff() {
    local owner="$1" repo="$2" pr="$3"

    if command -v gh &>/dev/null; then
        echo "Fetching PR diff via gh CLI..." >&2
        gh pr diff "$pr" --repo "$owner/$repo" 2>/dev/null
    else
        echo "Fetching PR diff via GitHub API..." >&2
        curl -sf -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.diff" \
            "https://api.github.com/repos/$owner/$repo/pulls/$pr" 2>/dev/null
    fi
}

# --- Build analysis prompt ---------------------------------------------------
build_prompt() {
    local owner="$1" repo="$2" pr="$3"
    local metadata="$4"
    local diff_file="$5"

    # Extract key metadata fields
    local title author state additions deletions changed_files
    title=$(echo "$metadata" | jq -r '.title // "Unknown"')
    author=$(echo "$metadata" | jq -r '.author.login // .user.login // "Unknown"')
    state=$(echo "$metadata" | jq -r '.state // "Unknown"')
    additions=$(echo "$metadata" | jq -r '.additions // "N/A"')
    deletions=$(echo "$metadata" | jq -r '.deletions // "N/A"')
    changed_files=$(echo "$metadata" | jq -r '.changedFiles // .changed_files // "N/A"')

    cat <<PROMPT
You are a senior software engineer performing a thorough code review on a GitHub Pull Request.
Analyze the diff below and produce a structured review.

PR: $owner/$repo#$pr
Title: $title
Author: $author
State: $state
Stats: +$additions / -$deletions across $changed_files file(s)

The full diff follows. Review it carefully for:
- Logic errors, bugs, and edge cases
- Security vulnerabilities (injection, auth, data exposure, etc.)
- Performance issues (N+1 queries, inefficient loops, missing indexes)
- Code quality (readability, maintainability, DRY violations)
- Testing gaps (missing tests for new/changed code)
- Breaking changes or API compatibility concerns
- Error handling and resilience

Your response MUST follow this exact format:

## Summary
[2-3 sentences summarizing what the PR does and your overall assessment]

## Identified Risks
- [Risk 1: description and severity]
- [Risk 2: description and severity]
...

## Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
...

## Confidence Score
[Low/Medium/High] — [brief explanation of why this confidence level]

DIFF:
$(cat "$diff_file")
PROMPT
}

# --- Run Claude analysis -----------------------------------------------------
run_claude_analysis() {
    local prompt_file="$1"
    local output_file="$2"

    echo "Running Claude Code analysis (model: $MODEL, timeout: ${TIMEOUT}s)..." >&2

    # Try claude-code first, fall back to claude
    if command -v claude-code &>/dev/null; then
        timeout "$TIMEOUT" claude-code --model "$MODEL" \
            --print "$(cat "$prompt_file")" \
            > "$output_file" 2>/tmp/claude-review-debug.log
    else
        timeout "$TIMEOUT" "$CLAUDE_BIN" --model "$MODEL" \
            -p "$(cat "$prompt_file")" \
            > "$output_file" 2>/tmp/claude-review-debug.log
    fi

    local exit_code=$?
    if [[ $exit_code -eq 124 ]]; then
        echo "WARNING: Claude analysis timed out after ${TIMEOUT}s." >&2
        echo "Try increasing --timeout or use a smaller PR." >&2
        return 1
    elif [[ $exit_code -ne 0 ]]; then
        echo "ERROR: Claude analysis failed (exit code: $exit_code)." >&2
        echo "Debug log: /tmp/claude-review-debug.log" >&2
        return 1
    fi
    return 0
}

# --- Format final output -----------------------------------------------------
format_output() {
    local raw_output="$1"
    local owner="$2" repo="$3" pr="$4"

    echo "============================================"
    echo "  CLAUDE CODE PR REVIEW"
    echo "  $owner/$repo#$pr"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""
    cat "$raw_output"
    echo ""
    echo "---"
    echo "Review generated by claude-review | Model: $MODEL"
}

# --- Simulated mode (when claude is unavailable) -----------------------------
simulated_review() {
    local owner="$1" repo="$2" pr="$3"
    local metadata="$4"
    local diff_file="$5"

    local title additions deletions changed_files
    title=$(echo "$metadata" | jq -r '.title // "Unknown"')
    additions=$(echo "$metadata" | jq -r '.additions // "N/A"')
    deletions=$(echo "$metadata" | jq -r '.deletions // "N/A"')
    changed_files=$(echo "$metadata" | jq -r '.changedFiles // .changed_files // "N/A"')

    echo "============================================"
    echo "  CLAUDE CODE PR REVIEW"
    echo "  $owner/$repo#$pr"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""
    echo "## Summary"
    echo "This PR ($title) introduces changes across $changed_files file(s)"
    echo "(+$additions / -$deletions). A cursory automated review was performed"
    echo "but Claude Code is not available for deep analysis. Install Claude Code"
    echo "for full AI-powered review capabilities."
    echo ""
    echo "## Identified Risks"
    echo "- Claude Code not available for automated risk detection"
    echo "- Manual review recommended before merging"
    echo "- Consider running: claude-review --pr $owner/$repo#$pr with Claude Code installed"
    echo ""
    echo "## Improvement Suggestions"
    echo "- Install Claude Code for comprehensive AI review"
    echo "- Review the diff manually for logic and security issues"
    echo "- Ensure adequate test coverage for changed code paths"
    echo ""
    echo "## Confidence Score"
    echo "Low — automated analysis limited without Claude Code; manual review required"
    echo ""
    echo "---"
    echo "NOTE: This is a simulated review. Install Claude Code (npm install -g @anthropic-ai/claude-code)"
    echo "and re-run for a full AI-powered analysis."
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    parse_args "$@"

    # Parse the PR URL
    OWNER="" REPO="" PR_NUMBER=""
    parse_pr_url "$PR_URL"

    echo "=== claude-review ==="
    echo "PR: $OWNER/$REPO#$PR_NUMBER"
    echo ""

    # Check dependencies (sets CLAUDE_AVAILABLE)
    check_deps

    # Create temp directory
    TEMP_DIR=$(mktemp -d -t claude-review-XXXXXX)
    local diff_file="$TEMP_DIR/diff.txt"
    local metadata_file="$TEMP_DIR/metadata.json"
    local prompt_file="$TEMP_DIR/prompt.txt"
    local output_file="$TEMP_DIR/output.md"

    # Fetch PR data
    echo "Fetching PR #$PR_NUMBER from $OWNER/$REPO..."
    fetch_pr_metadata "$OWNER" "$REPO" "$PR_NUMBER" > "$metadata_file" || {
        echo "ERROR: Failed to fetch PR metadata. Check the PR URL and authentication."
        exit 1
    }
    fetch_pr_diff "$OWNER" "$REPO" "$PR_NUMBER" > "$diff_file" || {
        echo "ERROR: Failed to fetch PR diff. Check the PR URL and authentication."
        exit 1
    }

    # Validate fetched data
    if [[ ! -s "$diff_file" ]]; then
        echo "ERROR: Empty diff. The PR may have no changes or authentication failed."
        exit 1
    fi

    local diff_size
    diff_size=$(wc -c < "$diff_file")
    echo "Diff fetched: $diff_size bytes"
    echo ""

    # Run simulated review if Claude is not available
    if ! $CLAUDE_AVAILABLE; then
        simulated_review "$OWNER" "$REPO" "$PR_NUMBER" "$(cat "$metadata_file")" "$diff_file"
        exit 0
    fi

    # Build and run the analysis
    build_prompt "$OWNER" "$REPO" "$PR_NUMBER" "$(cat "$metadata_file")" "$diff_file" > "$prompt_file"

    if run_claude_analysis "$prompt_file" "$output_file"; then
        format_output "$output_file" "$OWNER" "$REPO" "$PR_NUMBER"
    else
        echo ""
        echo "=== Falling back to simulated review ==="
        simulated_review "$OWNER" "$REPO" "$PR_NUMBER" "$(cat "$metadata_file")" "$diff_file"
        exit 1
    fi
}

main "$@"
