#!/usr/bin/env bash
# claude-review — AI-powered PR review agent
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123
#         ./claude-review.sh --pr owner/repo#123
#         ./claude-review.sh --diff "$(git diff main...feature)"
#
# Uses Claude Code to analyze a PR diff and produces a structured Markdown review
# with Summary, Pros, Cons, Suggestions, and Confidence score.

set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────
CLAUDE_REVIEW_AGENT="${CLAUDE_REVIEW_AGENT:-pr-reviewer}"
TIMEOUT="${TIMEOUT:-300}"

# ── Parse args ──────────────────────────────────────────────────────────────
PR_URL=""
DIFF_INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pr) PR_URL="$2"; shift 2 ;;
        --diff) DIFF_INPUT="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            cat <<'EOF'
claude-review — AI-powered PR review using Claude Code sub-agent

USAGE:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo#123
  claude-review --diff "$(git diff main...feature)"

OUTPUT:
  Structured Markdown review with:
  - Summary (1-2 sentences)
  - Pros (what's good about this change)
  - Cons (bugs, risks, anti-patterns)
  - Suggestions (actionable improvements)
  - Confidence score (Low / Medium / High)

REQUIRES: Claude Code CLI, GitHub CLI (for --pr mode)
EOF
            exit 0
            ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Get the diff ────────────────────────────────────────────────────────────
DIFF=""

if [[ -n "$PR_URL" ]]; then
    # Convert shorthand: owner/repo#123 → URL
    if [[ "$PR_URL" =~ ^([^/]+)/([^#]+)#([0-9]+)$ ]]; then
        PR_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/pull/${BASH_REMATCH[3]}"
    fi

    # Fetch diff via GitHub CLI
    if ! command -v gh &>/dev/null; then
        echo "Error: gh CLI not found. Install: brew install gh" >&2
        exit 1
    fi

    # Extract owner/repo/number from URL
    # https://github.com/owner/repo/pull/123
    if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        PR_NUM="${BASH_REMATCH[3]}"
        echo "Fetching diff for $OWNER/$REPO#$PR_NUM..."

        DIFF=$(gh pr diff "$PR_NUM" --repo "$OWNER/$REPO" 2>&1) || {
            echo "Error fetching PR diff. Make sure gh is authenticated." >&2
            exit 1
        }
        PR_TITLE=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json title -q '.title' 2>/dev/null || echo "Unknown")
        PR_AUTHOR=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json author -q '.author.login' 2>/dev/null || echo "Unknown")
    else
        echo "Error: Invalid PR URL format: $PR_URL" >&2
        echo "Expected: https://github.com/owner/repo/pull/123" >&2
        exit 1
    fi
elif [[ -n "$DIFF_INPUT" ]]; then
    DIFF="$DIFF_INPUT"
    PR_TITLE="Manual diff"
    PR_AUTHOR="local"
else
    echo "Error: Provide --pr URL or --diff content" >&2
    exit 1
fi

if [[ -z "$DIFF" ]]; then
    echo "Error: No diff content." >&2
    exit 1
fi

# ── Build the review prompt ─────────────────────────────────────────────────
REVIEW_PROMPT=$(cat <<PROMPT
You are a senior code reviewer. Review the following PR diff and produce a
structured Markdown review. Be thorough, constructive, and specific.

PR: $PR_TITLE
Author: $PR_AUTHOR

RULES:
1. Summary: 1-2 sentences. What does this PR do at a high level?
2. Pros: What's good? Be specific — mention patterns, readability, test coverage.
3. Cons: What's problematic? Bugs, security issues, race conditions, missing error handling, performance concerns, breaking changes.
4. Suggestions: Actionable improvements. "Add input validation for X" not "Improve validation."
5. Confidence: Low / Medium / High — how confident are you in this review?

FORMAT your response EXACTLY like this:

## Review Summary
[1-2 sentences]

## ✅ Pros
- [specific positive observation]
- [another positive observation]

## ⚠️ Cons
- [specific issue with file/line reference if possible]
- [another issue]

## 💡 Suggestions
- [actionable suggestion]
- [another suggestion]

## 📊 Confidence
**[Low/Medium/High]** — [one sentence why]

---

DIFF:
$DIFF
PROMPT
)

# ═══ Method 1: Use Claude Code with a configured agent ═════════════════════
# If .claude/agents/pr-reviewer.md exists, use named agent. Otherwise direct prompt.

if [[ -f ".claude/agents/${CLAUDE_REVIEW_AGENT}.md" ]] || [[ -f "$HOME/.claude/agents/${CLAUDE_REVIEW_AGENT}.md" ]]; then
    echo "Using configured agent: $CLAUDE_REVIEW_AGENT"
    REVIEW=$(claude -p "@${CLAUDE_REVIEW_AGENT} review this PR diff" \
        --max-turns 10 \
        --allowedTools "Read" \
        --timeout "$TIMEOUT" \
        --output-format text 2>&1 <<< "$REVIEW_PROMPT" || echo "Claude Code failed")
else
    echo "Reviewing with Claude Code (no agent configured — using direct prompt)..."
    REVIEW=$(claude -p "$REVIEW_PROMPT" \
        --max-turns 10 \
        --allowedTools "Read" \
        --timeout "$TIMEOUT" \
        --output-format text 2>&1 || echo "Claude Code failed")
fi

# ── Output ──────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT" ]]; then
    echo "$REVIEW" > "$OUTPUT"
    echo "Review saved to $OUTPUT"
else
    echo "$REVIEW"
fi
