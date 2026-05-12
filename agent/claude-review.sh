#!/usr/bin/env bash
# claude-review — CLI wrapper for Claude PR review agent
# Usage: ./claude-review.sh --pr https://github.com/owner/repo/pull/123

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2
    exit 1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "Error: ANTHROPIC_API_KEY is not set" >&2
    exit 1
fi

exec python3 "$DIR/claude-review.py" "$@"
