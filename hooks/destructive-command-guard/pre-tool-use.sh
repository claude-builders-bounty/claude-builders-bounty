#!/usr/bin/env bash
# Claude Code PreToolUse Hook executable wrapper
python3 "$(dirname "$0")/pre_tool_use_blocker.py" "$@"
