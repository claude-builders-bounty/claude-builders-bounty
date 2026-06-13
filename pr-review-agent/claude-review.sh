#!/usr/bin/env bash
# ===========================================================================
# claude-review.sh — Bash wrapper for claude-review.py
#
# Provides a clean CLI interface for the PR review agent.  Can be sourced
# as a function or run as a script.
#
# Usage:
#   ./claude-review.sh --pr https://github.com/owner/repo/pull/123
#   ./claude-review.sh --pr 123 --owner owner --repo repo
#   ./claude-review.sh --pr https://github.com/owner/repo/pull/123 --format json
#
# Environment:
#   GITHUB_TOKEN    — GitHub personal access token (required)
#   CLAUDE_REVIEW   — Path to claude-review.py (default: same dir as this script)
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${CLAUDE_REVIEW_PYTHON:-python3}"
REVIEW_PY="${CLAUDE_REVIEW:-${SCRIPT_DIR}/claude-review.py}"

# --- Colour helpers ---
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

usage() {
    cat <<EOF
${BOLD}claude-review${NC} — PR Review Agent for Claude Code

${DIM}Usage:${NC}
    $(basename "$0") --pr https://github.com/owner/repo/pull/123
    $(basename "$0") --pr 123 --owner owner --repo repo
    $(basename "$0") --pr https://github.com/owner/repo/pull/123 --format json

${DIM}Options:${NC}
    --pr URL         Full GitHub PR URL
    --owner OWNER    Repository owner (if not using --pr)
    --repo REPO      Repository name (if not using --pr)
    --pr-number NUM  PR number (if not using --pr)
    --token TOKEN    GitHub token (default: \$GITHUB_TOKEN)
    --format FMT     Output format: markdown (default) or json
    --help           Show this help

${DIM}Environment:${NC}
    GITHUB_TOKEN          GitHub personal access token
    CLAUDE_REVIEW_PYTHON  Python interpreter (default: python3)
    CLAUDE_REVIEW         Path to claude-review.py

${DIM}Examples:${NC}
    GITHUB_TOKEN=ghp_xxx ./claude-review.sh --pr https://github.com/org/repo/pull/42
    $(basename "$0") --pr https://github.com/org/repo/pull/42 --format json | jq .
EOF
    exit 0
}

# --- Parse args ---
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        *) ARGS+=("$1") ;;
    esac
    shift
done

# --- Check dependencies ---
if ! command -v "$PYTHON" &>/dev/null; then
    echo -e "${RED}Error:${NC} Python interpreter '$PYTHON' not found."
    echo "Set CLAUDE_REVIEW_PYTHON or install Python 3."
    exit 1
fi

if [ ! -f "$REVIEW_PY" ]; then
    echo -e "${RED}Error:${NC} claude-review.py not found at: $REVIEW_PY"
    echo "Set CLAUDE_REVIEW to the correct path."
    exit 1
fi

# --- Run ---
exec "$PYTHON" "$REVIEW_PY" "${ARGS[@]}"
