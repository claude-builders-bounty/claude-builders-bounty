#!/usr/bin/env bash
# Claude Code PR Reviewer CLI
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/claude_review.py" "$@"
